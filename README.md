# tp_redes_grupo05

## Descripción
El objetivo de este trabajo práctico es desarrollar una aplicación de red para comprender la comunicación entre procesos y el modelo de servicio de la capa de transporte hacia la capa de aplicación. Además, se aprenderá a usar la interfaz de sockets y los principios básicos de la transferencia de datos confiable (RDT).

## Integrantes del Grupo

- ADD LATER

## Configuración del Proyecto (Primera Vez)

Para configurar el proyecto por primera vez, ejecute el siguiente comando:
```bash
./run_mininet.sh build
```
## Inicio del Proyecto

Para iniciar el proyecto, utilice el siguiente comando:
```bash
./run_mininet.sh run
```

## Instalar plugin de Wireshark

Crear la siguiente carpeta

```bash
mkdir -p ~/.local/lib/wireshark/plugins
```

Una vez copiada, copiar el plugin en ese directorio

```bash
cp ./plugin.lua ~/.local/lib/wireshark/plugins
```

En caso de querer desarrollar el plugin, recomiendo ejecutar los siguintes comandos

Primero eliminamos el plugin si lo copiamos

```bash
rm ~/.local/lib/wireshark/plugins/plugin.lua
```

Segundo, creamos un link hard

```bash
ln ./plugin.lua ~/.local/lib/wireshark/plugins/plugin.lua
```

Luego, cada vez que realizamos un cambio sobre el archivo `./plugin.lua`, ejecutamos
la combinacion de teclas: `Ctrl + Shift + L` (Analyze > Reload Lua plugin) para reflejar
los cambios en Wireshark.

### _Troubleshooting_
Si encuentra inconvenientes al ejecutar el ejecutable `./run_mininet.sh`, intente ejecutarlo con privilegios de administrador utilizando `sudo`.

## Requerimientos
- Docker (versión 20.10 o superior)

## Testing

### Preparación del Entorno
1. Active el entorno virtual:
    ```bash
    source .venv/bin/activate
    ```

### Ejecución de Pruebas
2. Ejecute el script de pruebas:
    ```bash
    ./run_tests.sh
    ```

### Notas
- Asegúrese de que todas las dependencias estén instaladas antes de ejecutar las pruebas.
- Si encuentra problemas, verifique los permisos o la configuración del entorno virtual.
