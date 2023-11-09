describe('User journey of login, upload abstracts, perform search, view, visualisation and then delete search.', () => {
    beforeEach(() => {
        cy.visit('/');
        cy.viewport(1920, 1080);
    });

    // NB: Disabled for the test instance, as fixtures were only manually added to demo and prod vs part of a data migration.
    it('Lets login, go to results page, check its empty then try to upload an abstract file', () => {
        if (cy.notUsingTestServer()) {
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

            // goto results tab and make sure its empty

            cy.get('#side-menu')
                .contains('Results')
                .click()

            cy.get('.page-header')
                .should('have.text', 'Results')

            for (let i = 0; i < 30; i++) {
                var ready = cy.deleteAnyExistingResults()
                if (ready == true ){
                    break;
                }
                else {
                    cy.log("Retry refreshing results")
                }
            }

            cy.get('#results')
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
                .selectFile('tests/test-abstract-ovid-test-sample-5.txt')

            cy.get('#upload_button')
                .contains('Upload', { matchCase: false })
                .click()

            // We should be on the Select exposure MeSH® terms page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Select exposure MeSH® terms')

            // Lets add some exposure terms in the textarea, click add, then move on to mediators

            cy.get('#term_names').type('Public Health Systems Research;Humans');

            cy.contains('Add', { matchCase: false })
                .click()

            cy.contains('Save and move on to select mediators', { matchCase: false })
                .click()

            // We should be on the Select mediator MeSH® terms page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Select mediator MeSH® terms')

            // Lets add terms in the textarea, click add, then move on to outcomes

            cy.get('#term_names').type('Genetic Markers; Penetrance');

            cy.contains('Add', { matchCase: false })
                .click()

            cy.contains('Save and move on to select outcomes', { matchCase: false })
                .click()

            // We should be on the Select outcome MeSH® terms page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Select outcome MeSH® terms')

            // Lets add outcome term in the textarea, click add, move on to genes

            cy.get('#term_names').type('Neoplasm Metastasis;Eryptosis');

            cy.contains('Add', { matchCase: false })
                .click()

            cy.contains('Save and move on to select Genes and Filters', { matchCase: false })
                .click()

            // We should be on the Select genes and filter page

            cy.get('title')
                .invoke('text')
                .should('equal', 'TeMMPo: Select genes and filter')

            // click the button to continue and get some results

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

            for (let i = 0; i < 100; i++) {
                cy.checkForResults()
            }

            // this is where we navigate to the visualiations...

            // select sankey chart
            cy.get('#results tbody')
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


            // thats the end of visualiations test, now lets delete the file we uploaded...

            // goto results tab...

            cy.get('#side-menu')
                .contains('Results')
                .click()

            cy.get('.page-header')
                .should('have.text', 'Results')

            // find and click the delete button

            cy.get('.controls')
                .find('a.btn.btn-danger.btn-sm')
                .contains('Delete', { matchCase: false })
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
        }
    })
});