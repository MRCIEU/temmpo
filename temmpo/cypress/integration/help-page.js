describe('Checking expected home page content', () => {

    beforeEach(() => {
        cy.visit('/help/');
    });

    it('The help page has a title tag with expected text', () => {
        cy.get('title')
            .invoke('text')
            .should('equal', 'TeMMPo: Help')
    })

    it('The help page has h1 heading with expected text', () => {
        cy.get('.page-header')
            .invoke('text')
            .should('equal', 'Help')
    })

    it('Check we have 9x anchor links', () => {
        cy.get('.nav-pills')
            .find('li')
            .should('have.length', '9')
    })

    it('Click Overview link and confirm expected url', () => {
        cy.get('.nav-pills')
            .contains('Overview')
            .click()
        cy.url().should('include', '#overview') 
    })

    it('Click Upload articles link and confirm expected url', () => {
        cy.get('.nav-pills')
            .contains('Upload articles')
            .click()
        cy.url().should('include', '#upload') 
    })

    it('Click Specify exposures link and confirm expected url', () => {
        cy.get('.nav-pills')
            .contains('Specify exposures')
            .click()
        cy.url().should('include', '#exposures') 
    })

    it('Click Specify mechanisms link and confirm expected url', () => {
        cy.get('.nav-pills')
            .contains('Specify mechanisms')
            .click()
        cy.url().should('include', '#mechanisms') 
    })

    it('Click Specify outcomes link and confirm expected url', () => {
        cy.get('.nav-pills')
            .contains('Specify outcomes')
            .click()
        cy.url().should('include', '#outcomes') 
    })

    it('Click Genes and filter section link and confirm expected url', () => {
        cy.get('.nav-pills')
            .contains('Genes and filter section')
            .click()
        cy.url().should('include', '#genefilter') 
    })

    it('Click Navigate results section link and confirm expected url', () => {
        cy.get('.nav-pills')
            .contains('Navigate results')
            .click()
        cy.url().should('include', '#navigate') 
    })

    it('Click Re-use searches/abstracts section link and confirm expected url', () => {
        cy.get('.nav-pills')
            .contains('Re-use searches/abstracts')
            .click()
        cy.url().should('include', '#reuse') 
    })

    it('Click Changes section link and confirm expected url', () => {
        cy.get('.nav-pills')
            .contains('Changes')
            .click()
        cy.url().should('include', '#matchingchanges') 
    })

    it('Check we have a link to the changelog', () => {
        cy.get('.panel-body')
            .contains('CHANGELOG')
            .should('have.attr', 'href')
            .and('include', 'CHANGELOG')
    })

});