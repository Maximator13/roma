import { expect, test, type Page } from '@playwright/test'

function watchErrors(page: Page): string[] {
  const errors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  page.on('pageerror', (error) => errors.push(error.message))
  return errors
}

test('the collection opens from the header, draws the daily pack once and keeps it after a reload', async ({ page }) => {
  const errors = watchErrors(page)
  await page.goto('./')
  await page.getByRole('link', { name: 'Collection' }).click()
  await expect(page.getByRole('heading', { name: 'Collection', level: 1 })).toBeVisible()
  await expect(page.locator('.collection__stats')).toContainText(/^0 sur \d+ cartes/)

  const open = page.getByRole('button', { name: 'Ouvrir le paquet du jour' })
  await open.focus()
  await page.keyboard.press('Enter')
  await page.getByRole('button', { name: 'Briser le sceau' }).press('Enter')
  for (let index = 1; index <= 5; index += 1) {
    const back = page.getByRole('button', { name: `Retourner la carte ${index}` })
    await expect(back).toBeFocused()
    await page.keyboard.press('Enter')
  }
  const done = page.getByRole('button', { name: 'Ranger dans la collection' })
  await expect(done).toBeFocused()
  await expect(page.locator('.opening .rcard:not(.rcard--back)')).toHaveCount(5)
  await page.keyboard.press('Enter')

  await expect(page.locator('.collection__stats')).toContainText(/^5 sur \d+ cartes/)
  await expect(page.locator('.binder__grid .rcard')).toHaveCount(5)
  await page.reload()
  await expect(page.locator('.collection__stats')).toContainText(/^5 sur \d+ cartes/)
  await expect(page.getByRole('button', { name: 'Ouvrir le paquet du jour' })).toHaveCount(0)
  await expect(page.getByText(/Prochain paquet dans/)).toBeVisible()

  await page.locator('.binder__grid .binder__slot').first().click()
  const dialog = page.getByRole('dialog')
  await expect(dialog.locator('.card-dialog__text')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(dialog).toHaveCount(0)
  await expect(page).toHaveURL(/#\/collection$/)
  await page.keyboard.press('Escape')
  await expect(page.locator('.eras__button').first()).toBeVisible()
  expect(errors).toEqual([])
})

test('with reduced motion the pack opens straight onto its revealed cards', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('./#/collection')
  await page.getByRole('button', { name: 'Ouvrir le paquet du jour' }).click()
  await expect(page.locator('.opening--calm')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Briser le sceau' })).toHaveCount(0)
  await expect(page.locator('.opening .rcard:not(.rcard--back)')).toHaveCount(5)
})
