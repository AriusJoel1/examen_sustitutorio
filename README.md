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
- Los ejercicios y scripts de detección de drift (vistos en la Actividad5-CC3S2.md y Actividad16-CC3S2.md) muestran el uso de `terraform plan -detailed-exitcode` y planes guardados como evidencia (`plan_diff.txt`). Un drift no detectado puede introducir latencias inesperadas o rutas no auditadas que resulten en órdenes simultáneas a válvulas.

**Idempotencia.**  
Reaplicar la definición declarativa reproduce el mismo estado sin efectos secundarios peligrosos.  
- En una planta física, una operación no idempotente (por ejemplo, ejecutar un script imperativo que “abra válvulas” cada vez que se corre) puede duplicar acciones y producir sobrepresiones o estados incoherentes. La práctica con Terraform y módulos (lo vimos en la Actividad13-CC3S2.md) se usa para diseñar recursos idempotentes y permitir remediaciones seguras (`terraform apply -target=` cuando corresponde).

**Principio de menor privilegio.**  
Cada cuenta, SA o módulo solo tiene los permisos mínimos necesarios.  
- Permisos excesivos permiten que un operador o un servicio compromiseado envíe comandos peligrosos masivos. Las actividades de RBAC y NetworkPolicy (Actividad18-CC3S2.md, Actividad17-CC3S2.md) justifican políticas de separación de responsabilidades y reducción del blast radius.

---

### Por qué policy-as-code es obligatorio (mecanismo y beneficios)
1. **Bloqueo preventivo en PR:** Conftest/OPA en CI (Actividad10-CC3S2.md) impide merges que violen políticas (por ejemplo: `replicas > 1` sin etiqueta `approved`). Esto evita que cambios peligrosos lleguen al clúster.  
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

**Cómo lo evita IaC+policy-as-code:** bloqueo del PR y del apply para cambios que rompan invariantes, detección de drift y remediación automatizada, RBAC que evita accesos peligrosos y logging claro de quién y cuándo hizo cambios (Actividad13, Actividad16, Actividad10, Actividad18).

---

### Evidencias mínimas que deben acompañar la respuesta (qué presentar)
- `kubectl get all -n agua-inteligente` (estado actual de pods y deployments).  
- `evidence/terraform_plan.txt` o `evidence/plan_diff.txt` (salida de `terraform plan -detailed-exitcode`). (Véase Actividad5 y Actividad16).  
- `evidence/conftest_output.txt` (resultado de `conftest test` indicando bloqueo de regla). (Véase Actividad10).  
- `evidence/k8s_rbac.yaml` y `evidence/k8s_netpols.yaml` (export de objetos Kubernetes). (Véase Actividad17 y Actividad18).  
- Registro del remediado `evidence/remediation_<resource>.txt` producido por `safe_remediate.sh` (ejemplo en repo).

---

### Conclusión (resumen evaluativo)
Para sistemas con impacto físico la única postura responsable es adoptar IaC declarativa y policy-as-code como requisitos obligatorios: permiten prevenir cambios peligrosos, detectar drift, garantizar idempotencia en remediaciones y reducir el blast radius con controles de menor privilegio y pruebas en CI. Las actividades del repositorio (Actividad13, Actividad16, Actividad5, Actividad10, Actividad17, Actividad18 y la carpeta ejemplos/IaC-seguridad) suministran los patrones y scripts prácticos necesarios para implementar esta postura operativa.

---

### Referencias en el repositorio (ejemplos concretos)
- `Actividad13-CC3S2.md` — Terraform + gestión de secretos (Vault).  
- `Actividad16-CC3S2.md`, `Actividad5-CC3S2.md` — detección de drift y uso de `terraform plan -detailed-exitcode`.  
- `Actividad10-CC3S2.md` — Conftest / OPA en CI.  
- `Actividad17-CC3S2.md`, `Actividad18-CC3S2.md` — NetworkPolicy y RBAC.  
- `ejemplos/IaC-seguridad/` — scripts y tests (plantilla de evidencia).  

(Estos documentos y scripts están en el repositorio del curso y fueron utilizados como base para la implementación y evidencias entregadas).
