const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'https://py-web-d0.epi.bris.ac.uk',
    pageLoadTimeout: 100000,
    supportFile: 'cypress/support/commands.js',
    specPattern: 'cypress/integration/*.js',
    video: true,
    videoCompression: false,
  },
})