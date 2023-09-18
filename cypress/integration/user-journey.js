describe('User journey of login and upload abstracts, visualise then delete upload', () => {

    beforeEach(() => {
        cy.visit('/');
        cy.viewport(1920, 1080)
    });

    it('Lets login, go to results page, check its empty then try to upload an abstract file', () => {
            cy.visit('/logout');
            cy.visit('/');
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

        // goto results tab and check its empty

            cy.get('#side-menu')
                .contains('Results')
                .click()

            cy.get('.page-header')
                .should('have.text', 'Results')

            cy.get('table')
                .find('tr')
                .eq(1)
                .contains('No data available in table', { matchCase: false })

        // lets go to the search page try to upload an ovid medline abstract file

            cy.get('.controls')
                .find('a.btn.btn-default')
                .contains('New search', { matchCase: false })
                .click()

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Search')

            cy.get('.form-group')
                .find('a.btn.btn-primary')
                .eq(0)
                .contains('Upload OVID MEDLINE® formatted abstracts', { matchCase: false })
                .click()

        // Goes to the ovid medline abstract file upload page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Search Ovid MEDLINE®')

            cy.get('input[type=file]')
                .selectFile('test-abstract-ovid-test-sample-5.txt')

            cy.get('#upload_button')
                .contains('Upload', { matchCase: false })
                .click()

        // We should be on the Select exposure MeSH® terms page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Select exposure MeSH® terms')

        // Lets tick some exposure terms in the checkbox tree then move on to mediators

            cy.get('a')
                .contains('Organisms', { matchCase: false })
                .click()

            cy.contains('Save and move on to select mediators', { matchCase: false })
                .click()

        // We should be on the Select mediator MeSH® terms page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Select mediator MeSH® terms')

        // Lets tick mediator terms in the checkbox tree then move on to outcomes

            cy.get('a')
                .contains('Diseases', { matchCase: false })
                .click()

            cy.contains('Save and move on to select outcomes', { matchCase: false })
                .click()

        // We should be on the Select outcome MeSH® terms page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Select outcome MeSH® terms')

        // Lets tick an outcome term in the checkbox

            cy.get('a')
                .contains('Humanities', { matchCase: false })
                .click()

            cy.contains('Save and move on to select Genes and Filters', { matchCase: false })
                .click()

        // We should be on the Select genes and filter page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Select genes and filter')

        // Lets click on the dropdown filter

            cy.get('.selection')
                .click()
            cy.get('li')
                .contains('Body Regions > Breast', { matchCase: false })
                .click()

        // Lets click on the search button...

            cy.get('button.btn.btn-primary')
                .contains('Search', { matchCase: false })
                .click()

        // We should be on the my list of Results page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: My list')

        // get the table and check it has the uploaded text file listed

            cy.get('table')
                .eq(0)
                .find('tr')
                .eq(1)
                .should('not.be.empty')

        // now we are gonna wait a minute

            cy.wait(60000)

        // reload the page

            cy.reload()

        // this is where we will do the visualiations








        // now lets delete the file we uploaded

        // goto results tab and check its empty

            cy.get('#side-menu')
                .contains('Results')
                .click()

            cy.get('.page-header')
                .should('have.text', 'Results')

        // find and click the delete button

            cy.get('.controls')
                .find('a.btn.btn-danger.btn-sm')
                .contains('Delete', { matchCase: false })

        // have to force because possible bug where delete button is sometimes hidden in the table?
                .click({force:true})

        // now check we go the the delete search page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Delete search')

        // find the delete search button and click it

            cy.get('input.btn.btn-danger')
                .contains('Delete search', { matchCase: false })
                .click({force:true})

        // now were redirected to the results page with an alert saying Search results deleted

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: My list')

            cy.get('.info')
                .contains('Search results deleted', { matchCase: false })


    })

});