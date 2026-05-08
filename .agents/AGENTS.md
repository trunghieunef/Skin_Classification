# Repository Guidelines

## Project Structure & Module Organization
`src/` contains the core ML code: `dataset.py` for HAM10000 loading and splits, `model.py` for the EfficientNet-B3 classifier, `train.py` for the training loop, `evaluate.py` for metrics/plots, and `predict.py` for inference helpers. `web/` contains the Flask app in `app.py`, HTML templates in `web/templates/`, and static assets in `web/static/`. `notebooks/` is for EDA and Colab-based training. `data/` and `models/` hold local datasets, generated plots, and checkpoints and are intentionally ignored by Git.

## Build, Test, and Development Commands
Set up a local environment before working:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Common workflows:

```powershell
jupyter notebook notebooks/01_EDA.ipynb   # inspect data and splits
python web/app.py                         # run Flask app at http://localhost:5000
python -m compileall src web              # quick syntax smoke test
```

Training is documented in `notebooks/02_Training_Colab.ipynb`; contributors should treat that notebook as the supported training entrypoint unless they also add a local CLI wrapper.

## Coding Style & Naming Conventions
Use 4-space indentation, snake_case for functions/variables, PascalCase for classes, and descriptive module names that match the existing layout. Keep type hints where they already exist and prefer small, focused helper functions over large notebook-style blocks in `src/`. No formatter or linter is configured, so match the surrounding style and keep imports grouped and readable.

## Testing Guidelines
There is no dedicated `tests/` package yet. For changes in `src/`, run `python -m compileall src web` and perform a targeted smoke test through `web/app.py` or a small notebook script that exercises the changed code path. If you add tests, place them under a new `tests/` directory and use `test_<module>.py` naming.

## Commit & Pull Request Guidelines
Git history is currently minimal (`clean project`), so keep commit subjects short, imperative, and focused on one change, for example `add prediction input validation`. Pull requests should include a brief problem/solution summary, manual validation steps, and screenshots for `web/` UI changes. Note any impact on required local assets such as `data/HAM10000_metadata.csv` or `models/best_model.pth`.

## Security & Configuration Tips
Do not commit dataset contents, model weights, virtual environments, or `.env` files. Keep large artifacts in `data/` and `models/`, and document any new external dependency in `requirements.txt`.
