const detox = require('detox');
const config = require('../.detoxrc.js');
const adapter = require('detox/runners/jest/adapter');

jest.setTimeout(120000);
jasmine.getEnv().addReporter(adapter);

beforeAll(async () => {
  await detox.init(config, { initGlobals: false });
});

beforeEach(async () => {
  await adapter.beforeEach();
});

afterAll(async () => {
  await adapter.afterAll();
  await detox.cleanup();
});

// Global test helpers
global.waitForElement = async (element, timeout = 10000) => {
  await waitFor(element).toBeVisible().withTimeout(timeout);
};

global.tapElement = async (element) => {
  await element.tap();
};

global.typeText = async (element, text) => {
  await element.typeText(text);
};

global.scrollToElement = async (scrollView, element) => {
  await scrollView.scrollTo('bottom');
  await waitFor(element).toBeVisible();
};