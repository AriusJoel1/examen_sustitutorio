# Examen Sustitutorio

## Pregunta 1  
**Implementación de infraestructura basada en contenedores y Kubernetes**

### Descripción general  
En esta pregunta se implementó una infraestructura de microservicios utilizando contenedores Docker y orquestación con Kubernetes, desplegada localmente mediante **Minikube** sobre un entorno **Windows**. El objetivo fue validar la correcta configuración del clúster, la creación de recursos Kubernetes mediante manifiestos YAML y la verificación del estado operativo de los servicios desplegados.

---

### Preparación del entorno  
Se partió de un entorno limpio, donde previamente se instalaron y configuraron los siguientes componentes:

- **Docker Desktop** como motor de contenedores.
- **kubectl** como cliente de administración de Kubernetes.
- **Minikube** para crear un clúster Kubernetes local utilizando el driver Docker.
- **PowerShell** como terminal de ejecución.

El clúster se inicializó correctamente con el siguiente comando:

```bash
minikube start --driver=docker
