# Examen Sustitutorio 

## Pregunta 1

Explica por qué IaC declarativa con policy-as-code es obligatoria en este sistema 
Relaciona explícitamente drift, idempotencia y principio de menor privilegio con 
consecuencias operativas reales. 
Incluye un escenario de fallo grave causado por infraestructura imperativa.

## Respuesta

En un sistema que controla actuadores físicos (como nuestro escenario con válvulas, bombas, alarmas) la infraestructura declarativa (IaC) más policy-as-code es obligatoria porque garantiza **reproducibilidad**, **auditabilidad**, **bloqueo preventivo** de cambios peligrosos y **remediación trazable** tras incidentes. Sin estos controles, cambios manuales o improvisados pueden ejecutar secuencias de control que pongan en riesgo la seguridad física de la planta y las personas.

---

###  Relación técnica entre conceptos y consecuencias operativas

**Drift (estado real ≠ estado declarado).**  
Diferencia entre la configuración aplicada manualmente y la configuración declarada en el repositorio.  
- Si un operador escala `control-service` o modifica una NetworkPolicy manualmente, la topología de red y las reglas de control pueden dejar puertas abiertas para comandos no deseados hacia los actuadores.  
- Los ejercicios y scripts de detección de drift (vistos en la Actividad5 y Actividad16) muestran el uso de `terraform plan -detailed-exitcode` y planes guardados como evidencia (`plan_diff.txt`). Un drift no detectado puede introducir latencias inesperadas o rutas no auditadas que resulten en órdenes simultáneas a válvulas.

**Idempotencia.**  
Reaplicar la definición declarativa reproduce el mismo estado sin efectos secundarios peligrosos.  
- En una planta física, una operación no idempotente (por ejemplo, ejecutar un script imperativo que “abra válvulas” cada vez que se corre) puede duplicar acciones y producir sobrepresiones o estados incoherentes. La práctica con Terraform y módulos (lo vimos en la Actividad13) se usa para diseñar recursos idempotentes y permitir remediaciones seguras (`terraform apply -target=` cuando corresponde).

**Principio de menor privilegio.**  
Cada cuenta, SA o módulo solo tiene los permisos mínimos necesarios.  
- Permisos excesivos permiten que un operador o un servicio compromiseado envíe comandos peligrosos masivos. Las actividades de RBAC y NetworkPolicy (Actividad18, Actividad17) justifican políticas de separación de responsabilidades y reducción del blast radius.

---

### Por qué policy-as-code es obligatorio (mecanismo y beneficios)
1. **Bloqueo preventivo en PR:** Conftest/OPA en CI (Actividad10) impide merges que violen políticas (por ejemplo: `replicas > 1` sin etiqueta `approved`). Esto evita que cambios peligrosos lleguen al clúster.  
2. **Auditoría y evidencia:** los pipelines guardan los `terraform plan` y salidas de `conftest` como artefactos (ver ejemplos/IaC-seguridad), permitiendo reconstrucción forense post-incidente y cumplimiento.  
3. **Remediación automatizada o dirigida:** combinar detección de drift con playbooks de remediación (scripts `detect_drift.sh`, `safe_remediate.sh` del repo) permite corregir desviaciones sin detener la planta, reduciendo el impacto operacional.

---

###  Escenario de fallo grave (infraestructura imperativa — ejemplo concreto)
**Situación:** Un operador con acceso privilegiado ejecuta un script imperativo para “aumentar disponibilidad” y escala `control-service` a 12 réplicas desde la consola del servidor (no desde IaC). Simultáneamente, para “probar conectividad”, modifica una NetworkPolicy para permitir todo el tráfico desde una subred de pruebas.

**Cadena causal y efectos:**
1. Aumento repentino de réplicas del `control-service` produce múltiples instancias que ejecutan lógica de control simultánea.  
2. Sin coordinación mediante un orquestador idempotente y sin etiquetado/lock, varias instancias pueden emitir comandos concurrentes a las válvulas.  
3. La modificación manual de NetworkPolicy abre rutas que permiten a un servicio de reporting o a una máquina de pruebas inyectar comandos al bus de control.  
4. Resultado: maniobras concurrentes provocan un comando contradictorio que abre y cierra válvulas en paralelo —pérdida de integridad física—, generando derrames o daño en la planta.  
5. Por ausencia de registro estructurado (no hay `terraform plan` ni PR con revisión), la reconstrucción forense es lenta y ambigua.

**Cómo lo evita IaC+policy-as-code:** bloqueo del PR y del apply para cambios que rompan invariantes, detección de drift y remediación automatizada, RBAC que evita accesos peligrosos y logging claro de quién y cuándo hizo cambios (que lo vimos en las actividades Actividad16, Actividad18).

---

Finalmente, para sistemas con impacto físico la única postura responsable es adoptar IaC declarativa y policy-as-code como requisitos obligatorios: permiten prevenir cambios peligrosos, detectar drift, garantizar idempotencia en remediaciones y reducir el blast radius con controles de menor privilegio y pruebas en CI. Las actividades del repositorio (Actividad13, Actividad16, Actividad5, Actividad10, Actividad17, Actividad18 y la carpeta ejemplos/IaC-seguridad) suministran los patrones y scripts prácticos necesarios para implementar esta postura operativa.

---






## Pregunta 2

Diseña una estrategia técnica completa para: 
- detección automática de drift, 
- bloqueo preventivo de cambios manuales, 
- remediación segura sin detener la planta.

---

## Respuesta

La estrategia implementada se basa en **tres mecanismos complementarios**: bloqueo preventivo con policy-as-code, detección de drift en infraestructura declarativa y remediación controlada con mínimo impacto. Esta combinación es necesaria para sistemas que controlan componentes críticos y actuadores físicos, donde los errores de configuración tienen consecuencias operativas reales.

---

### 1. Bloqueo preventivo con Policy-as-Code

Se utilizan políticas declarativas con **Conftest / OPA** integradas en el flujo de CI para impedir que configuraciones peligrosas lleguen al clúster.

- Ejemplo de política: denegar `Deployment` con `replicas > 1` sin aprobación explícita.
- Herramienta: `conftest test k8s/manifests --policy policies/conftest`
- Beneficio: evita despliegues riesgosos antes del `merge`.

Este enfoque lo he utilizado en la actividad **Actividad10**, donde se introducio el uso de Policy-as-Code como mecanismo de control previo.

---

### 2. Detección de drift (estado real vs estado declarado)

Para identificar cambios manuales o no autorizados se emplea **detección de drift** mediante Terraform.

- Comando clave: `terraform plan -detailed-exitcode`
- Evidencia generada: `terraform_plan.txt` o `plan_diff.txt`
- Uso: detectar divergencias entre la infraestructura declarada y la infraestructura real.

Este mecanismo fue trabajado en **Actividad16**, donde se analiza el impacto operativo del drift y su detección temprana.

---

### 3. Remediación dirigida y controlada

Cuando se detecta drift, la remediación se realiza de forma **idempotente y dirigida**, evitando aplicar cambios globales innecesarios.

- Ejemplo: `terraform apply -target=<recurso>`
- Scripts de apoyo: `safe_remediate.sh`
- Objetivo: corregir solo el recurso afectado y minimizar el blast radius.

Estas prácticas se fundamentaron en clase en la **Actividad13**, donde se enfatiza la remediación segura y controlada.

---

### Relación con seguridad y menor privilegio

El uso de **RBAC y NetworkPolicies** asegura que solo los componentes autorizados puedan interactuar entre sí, reduciendo el impacto de errores o accesos indebidos.

Estas configuraciones corresponden a **Actividad17** y **Actividad18**, donde se aplican principios de menor privilegio y segmentación de red.

---

### Evidencia de estado real del clúster

A continuación se muestra la evidencia del estado actual del clúster, utilizada como línea base para detección de drift:

```bash
kubectl get nodes
kubectl get all -n agua-inteligente
kubectl describe deployment control -n agua-inteligente
kubectl describe deployment sensor -n agua-inteligente
```







## Pregunta 3

Define un estándar de repositorios IaC de misión crítica:
- estructura de carpetas,
- reglas de Pull Request y revisión,
- versionado de módulos,
- convenciones de naming con semántica operativa,
- gestión de secretos por entorno y por rol.
Incluye dos anti-patrones avanzados y explica cómo degradan la operación.

---

## Respuesta

En sistemas de misión crítica que interactúan con infraestructura y componentes físicos, el repositorio de IaC no es solo código: es un **artefacto operativo**. Un diseño incorrecto del repositorio incrementa el riesgo de drift, errores humanos, fallos no auditables y remediaciones inseguras. Por ello, se define el siguiente estándar obligatorio.

---

### Estructura de carpetas (separación por responsabilidad)

repo-iac/

├── modules/

│ ├── network/

│ ├── compute/

│ ├── security/

│ └── observability/

├── envs/

│ ├── dev/

│ ├── staging/

│ └── prod/

├── policies/

│ ├── conftest/

│ └── opa/

├── scripts/

│ ├── detect_drift.sh

│ └── safe_remediate.sh

├── evidence/

└── README.md


- `modules/`: lógica reusable, sin valores de entorno.
- `envs/`: ensamblaje por entorno (una sola fuente de verdad).
- `policies/`: policy-as-code que bloquea cambios peligrosos.
- `scripts/`: automatización controlada de detección y remediación.
- `evidence/`: salida auditable (planes, validaciones, logs).

Este enfoque lo hemos realizado explícitamente en **Actividad13** (modularización IaC) y **Actividad16** (detección de drift con evidencia).

---

### Reglas de Pull Request y revisión (controles humanos + automáticos)

Reglas obligatorias para repositorios de misión crítica:

- Prohibido `push` directo a `main`.
- PR obligatorio con:
  - al menos **2 revisores**,
  - uno con rol operativo (no solo desarrollador).
- CI debe ejecutar:
  - `terraform fmt`
  - `terraform validate`
  - `terraform plan -detailed-exitcode`
  - `conftest test`

Un PR solo puede aprobarse si **policy-as-code no detecta violaciones**.  
Esto fue aplicado en mi actividad **Actividad10**, donde se integra Conftest/OPA como bloqueo preventivo.

---

### Versionado de módulos 

- Versionado **semántico estricto**: `MAJOR.MINOR.PATCH`
- Regla:
  - `PATCH`: cambios internos sin impacto operativo.
  - `MINOR`: nuevos recursos compatibles.
  - `MAJOR`: cambios que alteran comportamiento físico u operacional.

Los entornos productivos **nunca** consumen módulos sin versión fija (`ref=tag`).  
Este principio se refuerzó y **Actividad13**, donde se analizan efectos de cambios no controlados.

---

### Convenciones de naming con semántica operativa

El nombre de un recurso debe describir su **impacto real**, no solo técnico.

Ejemplo:

k8s-prod-control-critical
netpol-prod-sensor-ingress-strict
rbac-prod-control-readonly


Beneficios:
- Permite evaluar riesgo solo leyendo el nombre.
- Reduce errores humanos en incidentes.
- Facilita auditoría post-fallo.

Estas convenciones se aplican junto a RBAC y NetworkPolicies, vistas en **Actividad17** y **Actividad18**.

---

### Gestión de secretos por entorno y por rol

Principios obligatorios:

- Nunca secretos en Git (ni en `tfvars`).
- Secretos separados por:
  - entorno (`dev`, `prod`),
  - rol (`control`, `sensor`, `ops`).
- Acceso controlado vía:
  - Kubernetes Secrets cifrados,
  - variables inyectadas en runtime,
  - permisos mínimos por ServiceAccount.

Este enfoque evita escalamiento lateral y se relaciona con prácticas vistas en **Actividad18** (menor privilegio).

---

### Anti-patrones avanzados (no triviales)

#### Anti-patrón 1: Módulos con lógica ambiental implícita

Un módulo cambia su comportamiento según el nombre del workspace o una variable oculta (`if env == prod then...`).

**Por qué degrada la operación:**
- El comportamiento real no es visible en el PR.
- Dificulta auditoría y pruebas.
- Puede activar configuraciones peligrosas sin revisión explícita.

**Impacto real:**  
Una remediación en `dev` puede comportarse distinto en `prod`, violando idempotencia y previsibilidad.

---

### Anti-patrón 2: Repositorio monolítico sin separación de blast radius

**Descripción:**  
Toda la infraestructura (red, cómputo, seguridad, observabilidad) en un solo `apply`.

**Por qué degrada la operación:**
- Un cambio pequeño puede forzar recreación masiva.
- Incrementa tiempo de recuperación ante fallos.
- Hace inviable remediación dirigida.

**Impacto real:**  
Ante un incidente, no es posible corregir un componente sin riesgo sistémico.

Este anti-patrón fue discutido indirectamente en **Actividad16**, al analizar el impacto de drift no localizado.

---

Finalmente, un repositorio IaC de misión crítica debe ser tratado como un sistema de control: con estructura clara, reglas estrictas, semántica operativa explícita y protección contra errores humanos. Las prácticas descritas están alineadas con las actividades del curso (Actividad5, Actividad10, Actividad13, Actividad16, Actividad17 y Actividad18) y son necesarias para garantizar seguridad, auditabilidad y estabilidad operacional.


## Pregunta 4

Diseña la arquitectura de módulos IaC aplicando patrones distintos para:
- infraestructura base,
- observabilidad,
- control operacional.
Justifica cada patrón en términos de:
- seguridad,
- resiliencia,
- costo cognitivo,
- reutilización.

---

## Respuesta

En sistemas de misión crítica, la arquitectura de módulos IaC debe reflejar **responsabilidades operativas reales**, no solo agrupaciones técnicas. Por ello, se diseña una arquitectura modular basada en **patrones distintos**, cada uno optimizado para su función, reduciendo el blast radius y el costo de error humano.

---

### 1. Módulo de Infraestructura Base  
**Patrón aplicado: Layered Core Infrastructure**

### Descripción
Este módulo define los recursos **fundacionales y de alta criticidad**, sobre los cuales todo el sistema depende:

- Red (VPC, subredes, políticas base)
- Clúster Kubernetes
- Identidad base (ServiceAccounts, roles raíz)
- Almacenamiento compartido

Ejemplo:
modules/base/

├── network.tf

├── cluster.tf

└── identity.tf



---

### Justificación

**Seguridad**  
- Cambios poco frecuentes y altamente controlados.
- Superficie de ataque mínima.
- Permite aplicar políticas estrictas desde el inicio.
  
**Resiliencia**  
- Al estar desacoplado de la lógica de negocio, evita recreaciones accidentales del clúster.
- Fallos en capas superiores no afectan la base.

**Costo cognitivo**  
- Los operadores saben que este módulo “no se toca” salvo cambios mayores.
- Reduce ambigüedad operativa.

**Reutilización**  
- Puede reutilizarse en múltiples proyectos con el mismo baseline.
  
Este patrón se trabajó en **Actividad13**, al separar infraestructura base de servicios y aplicaciones.

---

### 2. Módulo de Observabilidad  
**Patrón aplicado: Sidecar / Add-on Infrastructure Pattern**

### Descripción
Este módulo agrega capacidades de observabilidad sin modificar el comportamiento del sistema principal:

- Logging centralizado
- Métricas
- Alertas
- Dashboards

Ejemplo:

modules/observability/

├── metrics.tf

├── logging.tf

└── alerts.tf



---

### Justificación

**Seguridad**  
- Acceso de solo lectura a métricas y logs.
- No tiene permisos para modificar recursos críticos.

**Resiliencia**  
- Si el módulo falla, el sistema sigue operando.
- Observabilidad degradada ≠ sistema caído.

**Costo cognitivo**  
- Claramente identificado como “no funcional”.
- Facilita troubleshooting sin interferir en control.

**Reutilización**  
- Se puede acoplar o desacoplar a distintos entornos fácilmente.

Este patrón se relaciona con prácticas de monitoreo y evidencias vistas en **Actividad16**, donde se enfatiza la trazabilidad post-incidente.

---

### 3. Módulo de Control Operacional  
**Patrón aplicado: Control Plane Isolation Pattern**

### Descripción
Este módulo gestiona los componentes que **interactúan directa o indirectamente con sistemas físicos**:

- `control-service`
- `sensor-service`
- NetworkPolicies específicas
- RBAC restringido
- Límites de escalamiento

Ejemplo:
modules/control/

├── deployments.tf

├── rbac.tf

├── network


---

### Justificación

**Seguridad**  
- Principio de menor privilegio aplicado estrictamente.
- Segmentación de red explícita.
- Bloqueo de accesos no autorizados.

**Resiliencia**  
- Aislamiento evita fallos en cascada.
- Cambios en control no afectan infraestructura base.

**Costo cognitivo**  
- Operadores entienden que este módulo es el más sensible.
- Cambios requieren revisión reforzada.

**Reutilización**  
- Puede adaptarse a otros sistemas de control con mínima modificación.

Este patrón está alineado con **Actividad17 y Actividad18**, donde se trabajan RBAC, NetworkPolicies y control del blast radius.

---

### Comparación de patrones

| Módulo            | Patrón                      | Frecuencia de cambio | Riesgo   |
|-------------------|-----------------------------|----------------------|----------|
| Infraestructura   | Layered Core                | Muy baja             | Muy alto |
| Observabilidad    | Sidecar / Add-on            | Media                | Bajo     |
| Control           | Control Plane Isolation     | Alta (controlada)    | Crítico  |

---

En conjunto, esta arquitectura modular permite:
- aislar riesgos,
- reducir impacto de errores,
- facilitar remediaciones dirigidas,
- y mantener un bajo costo cognitivo operativo.

Las decisiones se fundamentan en las actividades del curso (**Actividad13, Actividad16, Actividad17 y Actividad18**) y están orientadas a sistemas con impacto físico real, donde la seguridad y la resiliencia son prioritarias.





## Pregunta 5

control-service depende de sensor-service pero no puede fallar de forma cascada.  
Explica y aplica:
- DIP (Dependency Inversion Principle),
- Circuit Breaker,
- Facade o Adapter (elegir uno).

Define contratos, invariantes y métricas mínimas obligatorias.

---

## Respuesta

En sistemas que interactúan con infraestructura física, una falla en cascada puede traducirse en **órdenes incorrectas, estados inconsistentes o daños materiales**. Por ello, la relación entre `control-service` y `sensor-service` debe diseñarse explícitamente para **fallar de forma segura**.

---

### 1. Aplicación del DIP (Dependency Inversion Principle)

### Diseño
`control-service` **no depende directamente** de la implementación concreta de `sensor-service`, sino de una **abstracción** (contrato).
ControlService → SensorPort (interface) ← SensorService


- `SensorPort` define qué información necesita el control.
- `SensorService` es solo una implementación intercambiable.

### Beneficios
- Permite reemplazar sensores físicos por simulados.
- Evita acoplamiento rígido.
- Facilita pruebas y escenarios de fallo.

Este principio fue aplicado conceptualmente en **Actividad17**, al desacoplar lógica central de dependencias externas.

---

### 2. Circuit Breaker (aislamiento de fallos)

### Problema
Si `sensor-service` empieza a responder lento o con errores, `control-service` **no debe bloquearse ni amplificar el fallo**.

### Solución
Se implementa un **Circuit Breaker lógico** con tres estados:
- **Closed**: llamadas normales.
- **Open**: llamadas bloqueadas tras umbral de fallos.
- **Half-Open**: pruebas controladas de recuperación.

### Política mínima
- Timeout estricto de lectura de sensores.
- Umbral de errores consecutivos.
- Ventana de enfriamiento antes de reintentar.

Este patrón evita fallos en cascada y es coherente con los ejercicios de resiliencia vistos en **Actividad16**.

---

### 3. Uso de Facade (elegido)

### Motivo
El Facade simplifica la interacción del `control-service` con múltiples sensores y reglas internas.

### Diseño
ControlService → SensorFacade → (SensorPort, Cache, Validadores)


### Ventajas
- Centraliza validaciones.
- Normaliza respuestas.
- Aplica fallback seguro si sensores fallan.

---

### 4. Contratos e invariantes

### Contrato SensorPort
- Entrega lecturas **normalizadas**.
- Nunca retorna valores fuera de rango físico.
- Siempre indica estado de confiabilidad.

### Invariantes obligatorias
- El control **nunca ejecuta acciones** con datos no validados.
- Ante error del sensor → estado seguro por defecto.
- El control no espera indefinidamente.

---

### 5. Métricas mínimas obligatorias

**Métricas técnicas**
- Latencia de lectura de sensor.
- Tasa de error del sensor.
- Estado del circuit breaker.

**Métricas operativas**
- Órdenes bloqueadas por seguridad.
- Activaciones de fallback.
- Eventos de degradación controlada.

Estas métricas están alineadas con prácticas de observabilidad vistas en **Actividad16**.

---

En conjunto, DIP + Circuit Breaker + Facade garantizan que `control-service` **nunca falle de forma cascada**, manteniendo la seguridad física del sistema.

---

## Pregunta 6

Diseña una estrategia de pruebas de IaC para sistemas físicos:
- qué pruebas NO automatizarías y por qué,
- qué pruebas deben correr en cada commit,
- cómo manejar flakiness,
- rollback probado bajo fallo parcial.
Incluye al menos 1 prueba de caos controlado.

---

## Respuesta

La estrategia de pruebas para sistemas con impacto físico debe priorizar **seguridad, realismo y control**, evitando automatizaciones peligrosas.

---

### 1. Pruebas que NO se automatizan

- Pruebas que implican **movimiento físico real** de actuadores.
- Simulaciones de fallo extremo (ej. corte eléctrico real).
- Ensayos que podrían dañar equipos.

Estas pruebas requieren supervisión humana y se realizan en ventanas controladas. Esta distinción fue discutida en **Actividad5**, al analizar riesgos operativos reales.

---

### 2. Pruebas en cada commit (obligatorias)

- Validación sintáctica (`terraform validate`).
- Detección de drift (`terraform plan -detailed-exitcode`).
- Policy-as-code con Conftest/OPA.
- Linting de YAML y manifests.

Estas prácticas se aplicaron en **Actividad10 y Actividad16**.

---

### 3. Manejo de flakiness

- Reintentos limitados y explícitos.
- Separar fallos infraestructurales de fallos lógicos.
- Etiquetar pruebas inestables.
- Ventanas de tolerancia para métricas no deterministas.

---

### 4. Rollback probado bajo fallo parcial

- Uso de `terraform apply -target` para reversión dirigida.
- Pruebas de rollback solo sobre módulos afectados.
- Validación post-rollback con métricas base.

Este enfoque se fundamenta en **Actividad13**, enfocada en remediación segura.

---

### 5. Prueba de caos controlado (ejemplo)

- Simular indisponibilidad del `sensor-service`.
- Verificar que `control-service`:
  - activa circuit breaker,
  - entra en modo seguro,
  - no emite comandos físicos.

Este tipo de prueba valida la resiliencia sin poner en riesgo el sistema real.

---

## Pregunta 7

Diseña el despliegue completo:
- Docker hardening extremo,
- Kubernetes con PSS, NetworkPolicies y RBAC,
- CI/CD local-first con freeze windows,
- estrategia de despliegue (justifica por qué NO usar canary si aplica).
Define alertas que protejan infraestructura física, no solo software.

---

## Respuesta

El despliegue de sistemas con impacto físico debe priorizar **previsibilidad y control**, no velocidad.

---

### 1. Docker hardening extremo

- Imágenes mínimas.
- Usuario no root.
- FS de solo lectura.
- Sin herramientas de debugging en producción.

Esto reduce superficie de ataque y errores humanos.

---

### 2. Kubernetes endurecido

- **Pod Security Standards (restricted)**.
- NetworkPolicies explícitas (deny-all por defecto).
- RBAC con mínimo privilegio.
- Separación estricta de namespaces.

Estas prácticas fueron aplicadas en **Actividad17 y Actividad18**.

---

### 3. CI/CD local-first con freeze windows

- Pruebas y validaciones ejecutadas localmente antes del push.
- Ventanas de freeze para cambios operativos.
- Despliegues solo con aprobación explícita.

Este enfoque reduce cambios impulsivos y errores fuera de horario.

---

### 4. Estrategia de despliegue

**No se usa canary** porque:
- Puede enviar órdenes contradictorias.
- Introduce múltiples comportamientos simultáneos.
- Aumenta riesgo físico.

Se prefiere:
- Rolling update controlado.
- Pausas manuales entre fases.

---

### 5. Alertas orientadas a infraestructura física

- Comandos bloqueados por seguridad.
- Activación de circuit breaker.
- Divergencia entre estado esperado y real.
- Latencia anómala de sensores.

Estas alertas protegen **el entorno físico**, no solo el software.

---

En conjunto, este despliegue prioriza seguridad, auditabilidad y control operativo, alineado con todas las actividades del curso y diseñado específicamente para sistemas de misión crítica.
