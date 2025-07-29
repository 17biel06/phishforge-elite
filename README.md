# PhishForge Elite 🔱

Una herramienta de simulación de phishing de código abierto para clonación de sitios web hiper-realistas y captura de datos en escenarios de pentesting ético.

---

## 🌟 Características Principales

| Característica | Descripción |
| :--- | :--- |
| **Interfaz Web Profesional** | Un panel de control limpio y moderno construido con Flask para gestionar campañas y datos capturados. |
| **Autenticación Segura** | Acceso protegido por usuario y contraseña, generados automáticamente en el primer uso. |
| **Clonación Avanzada** | Clona cualquier sitio web con alta fidelidad usando Selenium, capturando HTML, CSS y JS, y reescribiendo rutas para un realismo total. |
| **Sistema de Plantillas Modular** | Permite usar plantillas predefinidas (ej. Google) o añadir nuevas simplemente creando una carpeta. |
| **Captura en Tiempo Real** | Captura credenciales, IPs, User-Agents y más, con actualizaciones en vivo en el dashboard. |
| **Redirección Inteligente** | Tras la captura, redirige a la víctima a la URL legítima del sitio clonado o a una URL configurada en la plantilla. |
| **Almacenamiento Seguro** | Todos los datos capturados se cifran con Fernet antes de guardarse en una base de datos SQLite. |
| **Exportación de Datos** | Exporta los datos capturados de cada campaña a formatos CSV y JSON para análisis. |
| **Auto-Configurable** | Genera automáticamente los archivos y directorios necesarios en el primer arranque. |
| **Manejo de Errores Robusto** | Incluye manejo de excepciones en operaciones críticas para mayor estabilidad. |

---

## 🚀 Instalación y Uso

### 1. Prerrequisitos

- Python 3.10+
- `pip` (gestor de paquetes de Python)
- Un navegador web (Chrome, Firefox, etc.)

### 2. Instalación

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/17biel06/phishforge-elite.git
    cd phishforge-elite
    ```

2.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Instala el WebDriver:**
    PhishForge Elite necesita un WebDriver para que Selenium controle un navegador. Se recomienda ChromeDriver.
    - [Descargar ChromeDriver](https://chromedriver.chromium.org/downloads)
    - Asegúrate de que `chromedriver.exe` (o el ejecutable correspondiente) esté en el PATH de tu sistema.

### 3. Ejecución

1.  **Inicia la aplicación Flask:**
    ```bash
    python app.py
    ```
    **¡Importante!** La primera vez que ejecutes la aplicación, se generarán las credenciales de administrador (`usuario: admin`) y una contraseña aleatoria. **Guarda esta contraseña en un lugar seguro**, ya que solo se mostrará una vez en la consola.

2.  **Accede a la interfaz web:**
    Abre tu navegador y navega a `http://127.0.0.1:5000`.

### 4. Recuperación de Contraseña

Si olvidas la contraseña del administrador, puedes resetearla ejecutando el siguiente script desde la terminal:

```bash
python reset_admin_password.py
```

---

## 🛠️ ¿Cómo Funciona?

PhishForge Elite combina varias tecnologías para lograr simulaciones de phishing realistas:

- **Flask**: Proporciona el servidor backend y la interfaz de usuario.
- **Selenium**: Automatiza un navegador headless para realizar una clonación perfecta del sitio web objetivo, incluyendo todos sus recursos y contenido dinámico.
- **BeautifulSoup**: Analiza el HTML clonado para modificarlo de forma inteligente. Reescribe todas las rutas de recursos (CSS, imágenes) a rutas absolutas para preservar el estilo visual, neutraliza todos los scripts del lado del cliente y re-diseña la lógica de envío de formularios para apuntar al endpoint de captura local.
- **SQLite**: Una base de datos local almacena toda la información de las campañas y los datos capturados.
- **Cryptography (Fernet)**: Asegura que todos los datos sensibles capturados de los formularios se cifren antes de ser almacenados en la base de datos.

---

## 🤝 Contribución y Licencia

Este proyecto es de código abierto y está bajo la [Licencia MIT](LICENSE). Esto significa que eres libre de usar, modificar y distribuir este software. Si realizas cambios o mejoras, te pedimos amablemente que:

- **Mantengas el aviso de copyright original**.
- **Des crédito** a los autores originales (puedes enlazar a este repositorio).
- **Compartas tus mejoras** si consideras que pueden beneficiar a la comunidad.

¡Tus contribuciones son bienvenidas! Si encuentras un error o tienes una idea para una nueva característica, no dudes en abrir un *issue* o enviar un *pull request*.

---

## ⚖️ Aviso Legal

Esta herramienta está diseñada para **uso autorizado y ético únicamente**. Los desarrolladores no se hacen responsables de ningún mal uso o daño causado por esta herramienta. Siempre obtén permiso explícito y por escrito antes de realizar una simulación de phishing.