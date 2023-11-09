Cypress.Commands.add('checkForResults', () => {
    // Check if results have finsihed being generated, for up to 50 seconds
    cy.get('body').then(($body) => {
        if ($body.find('#un-processed-results').length > 0) {
            cy.log("Found pending results");
            // now we are gonna wait 1 second...
            cy.wait(1000);
            // reload the page by pressing the refresh button...
            cy.contains('Refresh', { matchCase: false })
                .click();
        }
        else
        {
            cy.log("No pending results");
        }
    })
})

Cypress.Commands.add('deleteAnyExistingResults', () => {
    // Check if results have finsihed being generated, for up to 50 seconds
    cy.get('body').then(($body) => {
        if ($body.find('a[data-test="delete-button"]').length > 0) {
            cy.get('a[data-test="delete-button"]').click()
            cy.get('input[type="submit"]').click()
        }
        else
        {
            cy.log("No existing results to delete");
        }
    })
})

Cypress.Commands.add('notUsingTestServer', () => {
    // Used to exclude running certain tests
    return ! ["https://py-web-t0.epi.bris.ac.uk", "https://app-dc2-tmpo-t0.epi.bris.ac.uk"].includes(Cypress.config("baseUrl"))
})