import assert from 'node:assert/strict';
import test from 'node:test';

import { materializeCssomStyles } from '../scripts/snapshot_cssom.ts';

function owner(id, replacements) {
  return {
    id,
    parentNode: {
      replaceChild(replacement, original) {
        replacements.push({ replacement, original });
      },
    },
  };
}

test('preserves stylesheet source URL, media condition, and cascade order', () => {
  const replacements = [];
  const firstOwner = owner('first', replacements);
  const secondOwner = owner('second', replacements);
  const appended = [];
  const document = {
    baseURI: 'https://example.test/page/index.html',
    styleSheets: [
      {
        href: 'https://example.test/css/main.css',
        media: { mediaText: 'screen and (min-width: 48rem)' },
        ownerNode: firstOwner,
        cssRules: [{ cssText: '.hero { background: url(../img/hero.png); }' }],
      },
      {
        href: 'https://cdn.example.test/theme/base.css',
        media: { mediaText: 'all' },
        ownerNode: secondOwner,
        cssRules: [{ cssText: '.button { color: red; }' }],
      },
    ],
    createElement() {
      return {
        attributes: {},
        textContent: '',
        setAttribute(name, value) {
          this.attributes[name] = value;
        },
      };
    },
    head: { appendChild(node) { appended.push(node); } },
    querySelectorAll() { return []; },
  };

  assert.equal(materializeCssomStyles(document), 2);
  assert.deepEqual(replacements.map(({ original }) => original.id), ['first', 'second']);
  assert.equal(appended.length, 0);
  assert.equal(
    replacements[0].replacement.textContent,
    '.hero { background: url("https://example.test/img/hero.png"); }\n',
  );
  assert.equal(
    replacements[0].replacement.attributes.media,
    'screen and (min-width: 48rem)',
  );
  assert.equal(
    replacements[0].replacement.attributes['data-source-url'],
    'https://example.test/css/main.css',
  );
  assert.equal(replacements[1].replacement.attributes.media, undefined);
});

test('uses the page document when Puppeteer invokes the function without arguments', () => {
  const previousDocument = globalThis.document;
  globalThis.document = {
    baseURI: 'https://example.test/page.html',
    styleSheets: [],
    head: { appendChild() {} },
    querySelectorAll() { return []; },
  };
  try {
    assert.equal(materializeCssomStyles(), 0);
  } finally {
    globalThis.document = previousDocument;
  }
});
