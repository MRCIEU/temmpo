const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: 'https://py-web-d0.epi.bris.ac.uk',
    supportFile: false,
    specPattern: 'cypress/integration/*.js',
    video: true,
    videoCompression: false,
  },
})