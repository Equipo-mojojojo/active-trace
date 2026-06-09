---
name: playwright-best-practices
description: Patrones E2E con Playwright para active-trace. Auth, Page Objects, selectores, mocking de API, CI.
license: MIT
---

# Playwright Best Practices — active-trace

## Setup y configuración

```typescript
// playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: "html",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
```

## Auth — fixture reutilizable

```typescript
// e2e/fixtures/auth.ts
import { test as base, expect } from "@playwright/test";
import type { Page } from "@playwright/test";

interface AuthFixtures {
  authenticatedPage: Page;
  coordinadorPage: Page;
}

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // Login programático via API — no via UI (más rápido y estable)
    const response = await page.request.post("/api/auth/login", {
      data: { email: "admin@test.com", password: "password123" },
    });
    const { access_token } = await response.json();

    // Inyectar token en localStorage antes de navegar
    await page.goto("/");
    await page.evaluate((token) => {
      localStorage.setItem("access_token", token);
    }, access_token);

    await use(page);
  },
});

export { expect };
```

## Page Object Model

```typescript
// e2e/pages/LoginPage.ts
import type { Page, Locator } from "@playwright/test";

export class LoginPage {
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(private page: Page) {
    this.emailInput = page.getByLabel("Email");
    this.passwordInput = page.getByLabel("Contraseña");
    this.submitButton = page.getByRole("button", { name: "Ingresar" });
    this.errorMessage = page.getByRole("alert");
  }

  async goto() {
    await this.page.goto("/login");
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}
```

## Selectores — orden de prioridad

```typescript
// 1. Por rol (accesible, recomendado)
page.getByRole("button", { name: "Enviar comunicación" });
page.getByRole("textbox", { name: "Asunto" });
page.getByRole("table");

// 2. Por label (formularios)
page.getByLabel("Email");

// 3. Por texto
page.getByText("Alumnos atrasados");

// 4. Por test-id (como último recurso, para elementos sin semántica)
page.getByTestId("tabla-atrasados");
// En el componente: <div data-testid="tabla-atrasados">

// EVITAR: selectores CSS frágiles
// page.locator(".table-row:nth-child(2)")  ← no hacer
// page.locator("#submit-btn")              ← no hacer
```

## Mocking de API — tests de componentes UI

```typescript
// e2e/tests/comunicaciones.spec.ts
import { test, expect } from "../fixtures/auth";

test("muestra preview antes de enviar", async ({ authenticatedPage: page }) => {
  // Mock del endpoint de preview
  await page.route("/api/comunicaciones/preview", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        asunto: "Recordatorio de entrega",
        destinatarios: 5,
        cuerpo_renderizado: "Estimado alumno...",
      }),
    });
  });

  await page.goto("/comunicaciones/nueva");
  await page.getByLabel("Asunto").fill("Recordatorio de entrega");
  await page.getByRole("button", { name: "Vista previa" }).click();

  await expect(page.getByText("Estimado alumno...")).toBeVisible();
  await expect(page.getByText("5 destinatarios")).toBeVisible();
});
```

## Tests E2E reales (con backend levantado)

```typescript
test("flujo completo: login → ver atrasados → enviar comunicación", async ({
  page,
}) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login("profesor@test.com", "password123");

  // Esperar navegación exitosa
  await expect(page).toHaveURL("/dashboard");

  // Navegar a atrasados
  await page.getByRole("link", { name: "Atrasados" }).click();
  await expect(page.getByRole("table")).toBeVisible();

  // Seleccionar alumno
  await page.getByRole("checkbox", { name: "Seleccionar Juan Pérez" }).check();

  // Enviar comunicación
  await page.getByRole("button", { name: "Enviar comunicación" }).click();
  await expect(page.getByText("Comunicación encolada")).toBeVisible();
});
```

## Assertions correctas

```typescript
// Esperar elemento visible — con timeout automático de Playwright
await expect(page.getByText("Guardado")).toBeVisible();

// Esperar navegación
await expect(page).toHaveURL("/dashboard");

// Verificar tabla tiene filas
const rows = page.getByRole("row");
await expect(rows).toHaveCount(6);  // 1 header + 5 data rows

// Verificar input tiene valor
await expect(page.getByLabel("Email")).toHaveValue("test@example.com");

// EVITAR: sleeps — Playwright ya espera automáticamente
// await page.waitForTimeout(2000);  ← no hacer
```

## Estructura de archivos E2E

```
e2e/
├── fixtures/
│   ├── auth.ts          ← fixtures de autenticación
│   └── data.ts          ← factories de datos de test
├── pages/
│   ├── LoginPage.ts
│   ├── DashboardPage.ts
│   └── ComunicacionesPage.ts
└── tests/
    ├── auth.spec.ts
    ├── atrasados.spec.ts
    └── comunicaciones.spec.ts
```

## CI — GitHub Actions

```yaml
- name: Run Playwright tests
  run: npx playwright test
  env:
    PLAYWRIGHT_BASE_URL: http://localhost:5173
    CI: true

- name: Upload report
  uses: actions/upload-artifact@v3
  if: failure()
  with:
    name: playwright-report
    path: playwright-report/
```
