# ACEest Fitness & Gym — DevOps CI/CD Assignment

A Flask-based fitness management API packaged with Docker and validated through Pytest, GitHub Actions, and Jenkins. This web/API version makes the application suitable for headless CI environments (the supplied starter scripts use Tkinter desktop UI, which is not available in standard containers).

## Features
- List fitness programs: Fat Loss, Muscle Gain, Beginner.
- Create and list clients, retrieve an individual client.
- Calculate estimated calories as `weight_kg × program factor` (22, 35, or 26).
- Record and retrieve weekly adherence progress.
- SQLite persistence, input validation, and automated tests.

## Local setup

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python app.py
```

Open `http://127.0.0.1:5000/` or `http://127.0.0.1:5000/health`.

## API examples

List programs:
```bash
curl http://127.0.0.1:5000/api/programs
```

Create a client:
```bash
curl -X POST http://127.0.0.1:5000/api/clients \
  -H "Content-Type: application/json" \
  -d '{"name":"Asha","age":28,"height":165,"weight":60,"program":"Fat Loss (FL)","target_adherence":80}'
```

Record progress (replace `1` with the returned client ID):
```bash
curl -X POST http://127.0.0.1:5000/api/clients/1/progress \
  -H "Content-Type: application/json" \
  -d '{"adherence":90,"week":"Week 41 - 2026","notes":"Good consistency"}'
```

## Run tests manually

```bash
python -m pytest -q
python -m compileall -q app.py tests
```

Tests use a temporary SQLite database; they do not modify your local application database.

## Docker

```bash
docker build -t aceest-fitness:local .
docker run --rm -p 5000:5000 -e ACEEST_DATABASE=/tmp/aceest.db aceest-fitness:local
```

Then visit `http://127.0.0.1:5000/health`. For persistent production data, mount a writable volume and set `ACEEST_DATABASE` to a file path inside that volume.

## Git and GitHub

Create a **public GitHub repository** named `aceest-fitness-cicd`, then from this directory run:

```bash
git init
git branch -M main
git add .
git commit -m "Build Flask fitness API with tests and CI pipeline"
git remote add origin https://github.com/YOUR_USERNAME/aceest-fitness-cicd.git
git push -u origin main
```

Suggested follow-up branch and commit:
```bash
git checkout -b feature/progress-validation
# make a small improvement, test it, then:
git add .
git commit -m "test: cover progress input validation"
git push -u origin feature/progress-validation
```

## GitHub Actions integration

`.github/workflows/main.yml` runs on pushes to `main`, `develop`, and `feature/**`, pull requests targeting `main`/`develop`, and manual dispatch. It checks out the repository, installs dependencies, compiles Python, runs Ruff linting and Pytest, builds a Docker image, then runs compile/lint/tests inside that image. Check the **Actions** tab in GitHub after pushing.

## Jenkins BUILD integration

`Jenkinsfile` checks out the configured source repository, installs Python test dependencies, compiles and tests the app, and builds a Docker image. To configure:
1. Install Jenkins and ensure the agent has Git, Python 3, pip, and Docker installed.
2. Ensure the Jenkins service account can run Docker (or use a properly configured Docker agent).
3. In Jenkins, choose **New Item → Pipeline**.
4. Select **Pipeline script from SCM**, choose Git, and paste your GitHub repository URL. Set branch to `*/main` and script path to `Jenkinsfile`.
5. Configure a GitHub webhook to `http(s)://YOUR_JENKINS_URL/github-webhook/` if the GitHub plugin is installed; alternatively the Jenkinsfile polls SCM every five minutes.
6. Click **Build Now** and inspect the stage logs. A webhook requires a reachable Jenkins URL; local-only Jenkins cannot receive GitHub webhooks.

The Jenkins pipeline requires the repository to be configured in Jenkins and a working Docker-enabled agent. The included file is pipeline configuration; it cannot run until your Jenkins server is configured.

## Deliverables checklist
- `app.py`, `requirements.txt`
- `tests/test_app.py`, `pytest.ini`, `requirements-dev.txt`
- `Dockerfile`, `.dockerignore`
- `.github/workflows/main.yml`
- `Jenkinsfile`
- `README.md`

## Security notes
This is an educational starter project. Before production use, add authentication/authorization, rate limiting, migrations, secrets management, database backups, and deployment-specific configuration. The calorie estimate is a simple assignment formula, not medical advice.
