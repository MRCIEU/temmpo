from datetime import datetime
import logging
import os
from selenium.common.exceptions import WebDriverException

from django.conf import settings
from django.core.files import File
from django.urls import reverse
from django.test import tag

from browser.matching import perform_search
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload, OVID, PUBMED, Gene
from tests.base_selenium_test_case import SeleniumBaseTestCase

logger = logging.getLogger(__name__)

@tag('selenium-test')
class BubbleChartJSTestCase(SeleniumBaseTestCase):
    """Test Bubble chart"""

    fixtures = ['test_searching_mesh_terms.json', 'test_genes.json', ]

    def _set_up_test_search_result(self):
        year = 2018
        test_file = open(os.path.join(os.path.dirname(__file__), 'test-abstract-ovid-test-sample-5.txt'), 'r')
        upload = Upload(user=self.user, abstracts_upload=File(test_file, u'test-abstract-ovid-test-sample-5.txt'), file_format=OVID)
        upload.save()
        test_file.close()

        exposure_terms = MeshTerm.objects.filter(term__in=("Humans", "Cells"), year=year)
        mediator_terms = MeshTerm.objects.get(term="Phenotype", year=year).get_descendants(include_self=True)
        outcome_terms = MeshTerm.objects.get(term="Apoptosis", year=year).get_descendants(include_self=True)

        gene = Gene.objects.get(name="TRPC1")

        # Create related criteria object
        search_criteria = SearchCriteria(upload=upload, mesh_terms_year_of_release=year)
        search_criteria.save()

        search_criteria.genes.add(gene)
        search_criteria.exposure_terms.set(exposure_terms)
        search_criteria.outcome_terms.set(outcome_terms)
        search_criteria.mediator_terms.set(mediator_terms)
        search_criteria.save()

        # Create search result object
        search_result = SearchResult(criteria=search_criteria)
        search_result.save()

        # Run the search
        perform_search(search_result.id)

        return SearchResult.objects.get(id=search_result.id)

    def test_bubble_chart(self):
        search_result = self._set_up_test_search_result()
        self.assertTrue(search_result.mediator_match_counts_v4 > 0)

        # Bubble chart page
        self.sel_open(reverse("results_bubble",  kwargs={'pk': search_result.id}))

        self.assertTrue("No matches found" not in self.driver.page_source)
        self.assertTrue("Filtered by " not in self.driver.page_source)

        screen_shot_name = "%stest_bubble_chart_%s.png" % (settings.RESULTS_PATH, datetime.now().isoformat())
        self.driver.save_screenshot(screen_shot_name)
        logger.debug("Saved a screen shot here: %s" % screen_shot_name)

        try:
            legend_item_1_label = self.driver.find_element_by_css_selector("#bubble_chart > div > div:nth-child(1) > div > svg > g:nth-child(4) > g:nth-child(2)")
            self.assertEqual(legend_item_1_label.get_attribute("column-id"), "1. Serogroup")  # Appears last in the file of matches but has the higher score.
        except WebDriverException as e:
            print(e)
            print(self.driver.page_source)
            self.fail("A selenium exception occurred trying to access a legend element in a bubble chart")

        try:
            chart_header_label = self.driver.find_element_by_css_selector("#bubble_chart > div > div:nth-child(1) > div > svg > g:nth-child(3) > text")
            self.assertTrue(search_result.mediator_match_counts_v4 < 20)
            self.assertEqual(chart_header_label.text, "Focused search results based on original score")
            self.assertFalse("(Top 20)" in chart_header_label.text)

        except WebDriverException as e:
            print(e)
            print(self.driver.page_source)
            self.fail("A selenium exception occurred trying to access the chart label element in a bubble chart")

        search_result.delete()