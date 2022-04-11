describe('Checking side nav links and content', () => {

    beforeEach(() => {
        cy.visit('/');
    });

    it('Check home link', () => {
        cy.get('#side-menu')
            .contains('Home')
            .click()
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Text Mining for Mechanism Prioritisation')
    })

    it('Check credits link', () => {
        cy.get('#side-menu')
            .contains('Credits')
            .click()
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Credits')
    })

    it('Check help link', () => {
        cy.get('#side-menu')
            .contains('Help')
            .click()
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Help')
    })

    it('Check register link', () => {
        cy.get('#side-menu')
            .contains('Register')
            .click()
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Register')
    })

    it('Check login link', () => {
        cy.get('#side-menu')
            .contains('Login')
            .click()
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Login')
    })

    it('Check we have a logo', () => {
        cy.get('.navbar-default')
            .find('img')
            .should('have.attr', 'src',)
            .should('include','TeMMpo-logo-RGB-web.png')
    })

});