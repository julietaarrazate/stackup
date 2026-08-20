import { test, expect, type Page } from "@playwright/test";

/**
 * Golden-path E2E: the full flow a real first-time user takes, through the
 * actual rendered UI end to end — register → workspace → vendor/service →
 * application → cost → the number shows up correctly on the dashboard.
 * Every previous phase validated its own layer (unit/integration tests
 * against the API); this is the one test proving those layers actually
 * compose into a working product through the browser.
 */

function uniqueEmail(tag: string): string {
  return `e2e-${tag}-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
}

async function registerAndLogin(page: Page, email: string): Promise<void> {
  await page.goto("/register");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Contraseña", { exact: true }).fill("Sup3rSecret!");
  await page.getByRole("button", { name: "Crear cuenta" }).click();
  await page.waitForURL("**/app");
}

test("register, build a full cost, see it on the dashboard", async ({ page }) => {
  const email = uniqueEmail("golden");
  await registerAndLogin(page, email);

  // Create workspace
  await page.getByLabel("Nombre del workspace").fill("Oído");
  await page.getByRole("button", { name: "Crear" }).click();
  await page.getByRole("link", { name: /Oído/ }).click();
  await page.waitForURL(/\/app\/[^/]+$/);

  const workspaceUrl = page.url();
  const workspaceId = workspaceUrl.split("/app/")[1];

  // Overview starts empty
  await expect(page.getByText("Todavía no hay costos cargados")).toBeVisible();

  // Create an application
  await page.goto(`${workspaceUrl}/applications`);
  await page.getByLabel("Nombre de la aplicación").fill("Oído App");
  await page.getByRole("button", { name: "Agregar" }).click();
  await expect(page.getByText("Oído App")).toBeVisible();

  // Create a vendor + service
  await page.goto(`${workspaceUrl}/vendors`);
  await page.getByLabel("Nuevo proveedor").fill("Vercel");
  await page.getByRole("button", { name: "Agregar" }).click();
  await expect(page.getByText("Vercel", { exact: true })).toBeVisible();
  await page.getByText("Vercel", { exact: true }).click();
  await page.getByLabel("Nuevo servicio").fill("Pro");
  await page.getByRole("button", { name: "Agregar servicio" }).click();
  await expect(page.getByText("Pro", { exact: true })).toBeVisible();

  // Create a cost tying application + vendor/service together
  await page.goto(`${workspaceUrl}/costs`);
  await page.getByLabel("Aplicación").selectOption({ label: "Oído App" });
  await page.getByLabel("Proveedor").selectOption({ label: "Vercel" });
  await page.getByLabel("Servicio").selectOption({ label: "Pro" });
  await page.getByLabel("Nombre del costo").fill("Vercel Pro");
  await page.getByLabel("Monto").fill("20.00");
  await page.getByRole("button", { name: "Agregar costo" }).click();
  await expect(page.getByText("US$ 20,00/mes")).toBeVisible();

  // The Overview dashboard reflects the real, computed total — not a mock
  await page.goto(workspaceUrl);
  await expect(page.getByText("Costo mensual total")).toBeVisible();
  await expect(page.getByText("US$ 20,00").first()).toBeVisible();
  await expect(page.getByText("US$ 240,00")).toBeVisible(); // annualized = 20 * 12

  // Logout, log back in — data persists under the same account
  await page.getByRole("button", { name: /Salir|Cerrar sesión/ }).click();
  await page.waitForURL("**/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Contraseña", { exact: true }).fill("Sup3rSecret!");
  await page.getByRole("button", { name: "Ingresar" }).click();
  await page.waitForURL("**/app");
  await expect(page.getByRole("link", { name: /Oído/ })).toBeVisible();

  test.info().annotations.push({ type: "workspace", description: workspaceId });
});

test("a workspace is invisible to a user who isn't a member of it", async ({
  browser,
}) => {
  const ownerCtx = await browser.newContext();
  const ownerPage = await ownerCtx.newPage();
  await registerAndLogin(ownerPage, uniqueEmail("owner"));
  await ownerPage.getByLabel("Nombre del workspace").fill("Privado");
  await ownerPage.getByRole("button", { name: "Crear" }).click();
  await ownerPage.getByRole("link", { name: /Privado/ }).click();
  await ownerPage.waitForURL(/\/app\/[^/]+$/);
  const privateWorkspaceUrl = ownerPage.url();
  await ownerCtx.close();

  const strangerCtx = await browser.newContext();
  const strangerPage = await strangerCtx.newPage();
  await registerAndLogin(strangerPage, uniqueEmail("stranger"));
  await strangerPage.goto(privateWorkspaceUrl);
  // Next.js notFound() renders the default 404 page — the stranger gets no
  // signal that the workspace exists, not a 403 that would confirm it does.
  await expect(strangerPage.getByText(/404|not found/i)).toBeVisible();
  await expect(strangerPage.getByText("Privado")).not.toBeVisible();
  await strangerCtx.close();
});
