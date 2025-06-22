# PyGameWorkShopGame

A 3D game engine and workshop project built with Pygame and OpenGL. This project provides a foundation for creating 3D games, with features for model loading, rendering, and game object management.

## Features

*   **3D Model Loading:** Supports loading 3D models in `.glb` formats.
*   **OpenGL Rendering:** Utilizes OpenGL for efficient 3D rendering.
*   **Game Object Management:** A system for managing game objects and their properties.
*   **Window Management:**  Provides a windowing system based on Pygame.
*   **Event Handling:**  Includes a system for handling window events like close events.
*   **Configurable:** Easily configurable and extendable due to the modular design.
*   **Testing:** Includes a suite of tests to ensure code quality and stability.
*   **Documentation:**  Well-documented code and project structure.

## Installation

1.  **Prerequisites:**

    *   Python 3.x
    *   Pygame (`pip install pygame`)
    *   PyOpenGL (`pip install PyOpenGL`)
    *   PIL (Pillow) (`pip install Pillow`)
    *   Numpy (`pip install numpy`)

2.  **Clone the Repository:**

    ```bash
    git clone <repository_url>
    cd PyGameWorkShopGame
    ```

3.  **Install Dependencies:**

    While the project doesn't explicitly list dependencies in a `requirements.txt` file, ensure you have the necessary packages installed using pip:

    ```bash
    pip install pygame PyOpenGL Pillow numpy
    ```

## Usage

1.  **Running the Game:**

    Navigate to the `src` directory and execute the main script (if one exists) or a relevant example script.  For example (if a `main.py` exists):

    ```bash
    python src/main.py
    ```

    *Note:* Replace `main.py` with the actual entry point of your game.

2.  **Example Code Snippet:**

    ```python
    # Example usage of the Model class (assuming src/Model.py exists)
    from src.Model import Model
    from src.opengl_util import glBufferStatus #example

    # Load a model
    model = Model("res/your_model.glb") # Replace with your model path

    # Access model data (example)
    vertices = model.vertices
    indices = model.indices

    # Example using glBufferStatus
    buffer_status = glBufferStatus(1024, GL_STATIC_DRAW)
    print(f"Buffer Size: {buffer_status.size}")
    ```

## Project Structure

```
PyGameWorkShopGame/
├── res/                # Resources (models, textures, etc.)
│   ├── <model>.fbx     # Example model file
│   ├── <model>.glb     # Example model file
│   └── ...
├── src/                # Source code
│   ├── GameObject.py
│   ├── GameObjectSystem.py
│   ├── Model.py
│   ├── Window.py
│   ├── opengl_util.py
│   ├── ...             # Other game logic and engine components
│   └── main.py         # (Optional) Main entry point
├── .gitignore          # Specifies intentionally untracked files that Git should ignore
├── LICENSE             # License information
├── README.md           # This file
└── ...
```

**Description of Key Directories:**

*   `res/`: Contains all the resources required for the game, such as 3D models (`.fbx`, `.glb`), textures, and other assets.
*   `src/`: Contains the Python source code for the game engine and game logic. This includes modules for game object management, model loading, rendering, window management, and input handling.

## Requirements/Dependencies

*   **Python:**  Version 3.x is required.
*   **Pygame:** Used for window management and input handling.
*   **PyOpenGL:** Used for 3D rendering with OpenGL.
*   **PIL (Pillow):** Used for image loading and processing.
*   **Numpy:** Used for numerical computations, especially for handling vertex data and matrices.

## Contributing

We welcome contributions to the PyGameWorkShopGame project! Please follow these guidelines:

1.  **Fork the Repository:** Create your own fork of the repository.
2.  **Create a Branch:** Create a new branch for your feature or bug fix.
3.  **Make Changes:** Implement your changes, ensuring code quality and adhering to the project's coding style.
4.  **Test Your Changes:**  Run the tests and ensure they pass.  Write new tests if necessary.
5.  **Commit Your Changes:** Commit your changes with clear and concise commit messages.
6.  **Submit a Pull Request:** Submit a pull request to the main repository, explaining your changes and their benefits.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
