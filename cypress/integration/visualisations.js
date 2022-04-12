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



    // Logout

        cy.get('#side-menu')
            .contains('Logout')
            .click()
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Login')


    })

});