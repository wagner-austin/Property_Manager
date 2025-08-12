# Lancaster 12 Lots - Makefile
# Cross-platform build commands

# Force bash for shell commands (needed for conditionals on Windows)
# Note: Requires Git Bash or WSL on Windows
SHELL := bash
.SHELLFLAGS := -c

# Variables (override like: make PORT=9000 serve)
PORT ?= 8000
OUT ?= deployment.zip
FOLDER_ID ?= 1iXsOCeIYZAK3DGknFOYZENNATpyavLW-

.PHONY: help serve stop status pack clean test check urls apply deps drive-login drive-apply \
        audit new lint lint-check mypy

help:
	@echo "Available commands:"
	@echo "  make serve       - Start local dev server in background (PORT=$(PORT))"
	@echo "  make stop        - Stop the background server"
	@echo "  make status      - Check if server is running"
	@echo "  make drive-apply - AUTO-FETCH Drive IDs and update site (RECOMMENDED)"
	@echo "  make drive-login - One-time Google Drive API setup"
	@echo "  make deps        - Install Python dependencies"
	@echo "  make lint        - Auto-fix and format all code (Python + JS/CSS)"
	@echo "  make lint-check  - Check code quality without fixing (for CI)"
	@echo "  make pack        - Create deployment package (OUT=$(OUT))"
	@echo "  make clean       - Remove generated files"
	@echo "  make test        - Check all files exist"

serve:
	@echo "Starting server at http://localhost:$(PORT)/?site=lancaster-12"
	@python -c "import webbrowser; webbrowser.open('http://localhost:$(PORT)/?site=lancaster-12')"
	@python -m http.server $(PORT)

debug:
	@echo "Starting server in DEBUG mode at http://localhost:$(PORT)/?site=lancaster-12&debug=1"
	@echo "📝 Debug logs will appear in browser console"
	@python -c "import webbrowser; webbrowser.open('http://localhost:$(PORT)/?site=lancaster-12&debug=1')"
	@python -m http.server $(PORT)

stop:
	@echo "Stopping server..."
	@powershell -NoProfile -ExecutionPolicy Bypass -File scripts\serve.ps1 stop 2>nul || bash scripts/serve.sh stop

status:
	@powershell -NoProfile -ExecutionPolicy Bypass -File scripts\serve.ps1 status 2>nul || bash scripts/serve.sh status

pack:
	@echo "Packaging → $(OUT)"
	@bash scripts/create-deployment.sh $(OUT) 2>/dev/null || cmd //c scripts\\create-deployment.bat

clean:
	@echo "Cleaning generated files..."
	@rm -f deployment.zip
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@find . -name "Thumbs.db" -delete 2>/dev/null || true
	@find . -name "desktop.ini" -delete 2>/dev/null || true
	@echo "✅ Cleaned"

test:
	@echo "Checking required files..."
	@test -f index.html || (echo "❌ Missing: index.html" && exit 1)
	@test -d css || (echo "❌ Missing: css/" && exit 1)
	@test -f css/styles.css || (echo "❌ Missing: css/styles.css" && exit 1)
	@test -d js || (echo "❌ Missing: js/" && exit 1)
	@test -f js/app-multisite.js || (echo "❌ Missing: js/app-multisite.js" && exit 1)
	@test -d sites/lancaster-12 || (echo "❌ Missing: sites/lancaster-12/" && exit 1)
	@test -f sites/lancaster-12/data.json || (echo "❌ Missing: sites/lancaster-12/data.json" && exit 1)
	@echo "✅ All required files present"

check:
	@echo "Checking Drive placeholders in site data..."
	@count=$$(grep -c "FILE_ID_OR_URL" sites/lancaster-12/data.json || true); \
	if [ "$$count" -gt 0 ]; then \
		echo "⚠️  $$count placeholders still need Drive links"; \
		echo "Run: make urls  to get Drive links automatically"; \
		exit 1; \
	else \
		echo "✅ No placeholders found - all Drive links configured!"; \
	fi

urls:
	@echo "Generating URL template for PDFs..."
	@python -m scripts.generate_url_template -o urls.json --csv urls.csv

apply:
	@echo "Applying URLs to site data..."
	@python -m scripts.update_site_data --site $(or $(SITE),lancaster-12)
	@echo "Site data updated! Refresh browser to see changes."

deps:
	@echo "Installing Google Drive API dependencies..."
	@python -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

drive-login: deps
	@echo "Setting up Google Drive API access..."
	@python -m scripts.setup_drive_api

drive-apply:
	@echo "Fetching real Drive IDs and updating site..."
	@python -m scripts.get_drive_ids --site=$(or $(SITE),lancaster-12) $(if $(FOLDER),--folder=$(FOLDER),)

audit:
	@echo "Auditing Drive folder vs subfolder '$(or $(CHILD),Public)'..."
	@python -m scripts.audit_drive_files \
		$(if $(FOLDER),--folder $(FOLDER),) \
		--child "$(or $(CHILD),Public)" \
		--include-images \
		--csv file-mapping.csv \
		--output file-mapping.json

new:
	@if [ -z "$(SITE)" ]; then \
		echo "Usage: make new SITE=palmdale-8"; \
		echo "Example: make new SITE=ranchita-20"; \
		exit 1; \
	fi
	@echo "Creating new site: $(SITE)"
	@mkdir -p "sites/$(SITE)"
	@if [ -f "sites/_template/data.json" ]; then \
		cp "sites/_template/data.json" "sites/$(SITE)/data.json"; \
		echo "✅ Created sites/$(SITE)/data.json"; \
		echo ""; \
		echo "Next steps:"; \
		echo "1. Edit sites/$(SITE)/data.json with property details"; \
		echo "2. Set drive.publicFolderId to your Public folder ID"; \
		echo "3. Run: make drive-apply SITE=$(SITE)"; \
		echo "4. Test with: make serve"; \
		echo "5. Open: http://localhost:$(PORT)/index.html?site=$(SITE)"; \
	else \
		echo "Error: Template not found at sites/_template/data.json"; \
		exit 1; \
	fi

# Tool shims (override if needed: make POETRY=... ESLINT=... PRETTIER=...)
POETRY ?= poetry
ESLINT ?= npx --yes eslint
PRETTIER ?= npx --yes prettier

# ---- Lint and auto-fix ----
lint:
	@echo "=== Running linters and auto-fixing issues ==="
	@echo.
	@echo "1) Ruff auto-fixing Python issues..."
	-@$(POETRY) run ruff check scripts/ --fix --unsafe-fixes
	@echo.
	@echo "2) Black formatting Python..."
	@$(POETRY) run black scripts/
	@echo.
	@echo "3) MyPy type checking..."
	-@$(POETRY) run mypy scripts/
	@echo.
	-@if exist package.json ( \
		echo "4) ESLint auto-fixing JS..." & \
		$(ESLINT) "js/**/*.js" --fix & \
		echo. & \
		echo "5) Prettier formatting JS/CSS/HTML..." & \
		$(PRETTIER) --write "js/**/*.js" "css/**/*.css" "index.html" \
	) else ( \
		echo "No package.json found; skipping JS/CSS formatting." \
	)
	@echo "✅ Linting and formatting complete!"

# ---- Just check without fixing (for CI or pre-commit) ----
lint-check:
	@echo "=== Checking code quality (no auto-fix) ==="
	@$(POETRY) run black --check scripts/
	@$(POETRY) run ruff check scripts/
	@$(POETRY) run mypy scripts/
	@if [ -f package.json ]; then \
		$(ESLINT) "js/**/*.js"; \
		$(PRETTIER) --check "js/**/*.js" "css/**/*.css" "index.html"; \
	fi

# ---- MyPy standalone ----
mypy:
	@echo "Running MyPy type checker..."
	@$(POETRY) run mypy scripts/
	@echo "✅ Type checking complete"