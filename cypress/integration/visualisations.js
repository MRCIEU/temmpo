describe('Checking visualiations', () => {

    beforeEach(() => {
        cy.visit('/');
    });

    it('Click login link, verify on the right page then try to login to admin', () => {
        cy.get('#side-menu')
            .contains('Login')
            .click()
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Login')

        cy.get('#id_username').type(Cypress.env('CREDENTIALS_USR'));
        cy.get('#id_password').type(Cypress.env('CREDENTIALS_PSW'));
        cy.get('button[type=submit]').click()

        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: My list')

    // goto resuts tab

        cy.get('#side-menu')
            .contains('Results')
            .click()

        cy.get('.page-header')
            .should('have.text', 'Results')


    // select sankey chart

        cy.get('tbody')
            .contains('View Sankey diagram')
            .click()


    // check sankey chart contains human....etc

        cy.get('#sankey_multiple')
            .should('include.text', 'Humans')
            .and('include.text', 'Genetic Markers')
            .and('include.text', 'Public Health Systems Research')


    // go back to results tab

        cy.get('#side-menu')
            .contains('Results')
            .click()

        cy.get('.page-header')
            .should('have.text', 'Results')

    // select bubble chart

        cy.get('tbody')
            .contains('View bubble chart')
            .click()

    // should contain Genetic Markers on the page

        cy.get('#bubble_chart')
            .should('include.text', 'Genetic Markers')

    // Let's logout now

        cy.get('#side-menu')
            .contains('Logout')
            .click()
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Login')


    })

});