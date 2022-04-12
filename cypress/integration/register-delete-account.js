describe('Register and delete an account', () => {

    beforeEach(() => {
        cy.visit('/');
    });

    it.skip('Click register link, verify on the right page then try to create an account', () => {
        cy.get('#side-menu')
            .contains('Register')
            .click()
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Register')

        cy.get('#id_username').type(Cypress.env('REGDELETE_USR'));
        cy.get('#id_email').type(Cypress.env('REGDELETE_EMAIL'));
        cy.get('#id_password1').type(Cypress.env('REGDELETE_PSW'));
        cy.get('#id_password2').type(Cypress.env('REGDELETE_PSW'));
        // cy.get('button[type=submit]').click()
        // cy.url().should('include', '/register/complete') 


    })

});