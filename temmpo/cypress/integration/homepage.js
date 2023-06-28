describe('Checking expected home page content', () => {

    beforeEach(() => {
        cy.visit('/');
    });

    it('The homepage has a title tag with expected text', () => {
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Text Mining for Mechanism Prioritisation')
    })

    it('The homepage has h1 heading with expected text', () => {
        cy.get('.page-header')
            .invoke('text')
            .should('equal', 'About TeMMPo')
    })

});