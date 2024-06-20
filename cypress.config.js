const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'https://app-dc2-tmpo-d0.epi.bris.ac.uk',
    pageLoadTimeout: 10000,
    redirectionLimit: 1000,
    supportFile: 'cypress/support/commands.js',
    specPattern: 'cypress/integration/*.js',
    video: true,
    videoCompression: false,
  },
})