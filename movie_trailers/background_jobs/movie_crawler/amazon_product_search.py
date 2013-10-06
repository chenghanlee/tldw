from amazonproduct.api import API
from fuzzywuzzy import fuzz
from lxml import etree

class AmazonProductSearch():
    def __init__(self, aws_access_key, aws_secret_key, affiliate_key):
        self.api = API(aws_access_key, aws_secret_key, 'us', affiliate_key)

    def _create_product(self, result):
        product = {}
        product['ASIN'] = str(result.ASIN)
        product['Amount'] = str(result.OfferSummary.LowestNewPrice.Amount)
        product['Binding'] = str(result.ItemAttributes.Binding)
        product['DetailPageURL'] = str(result.DetailPageURL)
        return product

    def item_search(self, title, actor, expected_running_time,
            ResponseGroup='OfferFull, Medium', release_year=None):
        '''
        This method searches Amazon for DVD, Blu-ray, and/or Amazon Instant
        Video listings of the movie that we are searching. Actor and running
        time are included in the query to improve the accuracy of the results
        returned by Amazon.

        Args:
            title: Title of the movie
            actor: Top billing actor for the movie
            expected_running_time: Total running time for the movie
            ResponseGroup: See response group in amazon product search api
                documentation
        '''
        try:
            results = self.api.item_search('DVD', actor=actor, Keywords=title,
                         ResponseGroup=ResponseGroup)
        except Exception as e:
            print e
            return []
        
        rv = []
        max_release_year_diff = 1
        max_running_time_diff = 5
        bindings_seen = {"DVD": False, "Blu-ray": False,
                         "Amazon Instant Video": False}

        for result in results:
            etree.tostring(result, pretty_print=True)
            try:
                if all(bindings_seen.values()):
                    return rv

                result_binding = str(result.ItemAttributes.Binding)
                result_release_year = int(str(result.ItemAttributes.ReleaseDate).split('-')[0])
                result_running_time = int(result.ItemAttributes.RunningTime)
                result_title = str(result.ItemAttributes.Title)
                
                if fuzz.partial_ratio(title.lower(), result_title.lower()) < 100:
                    continue
                if release_year is not None and abs(release_year - result_release_year) > max_release_year_diff:
                    continue
                if abs(expected_running_time - result_running_time) > max_running_time_diff:
                    continue
                if result_binding not in bindings_seen.keys():
                    continue
                if bindings_seen.get(result_binding):
                    continue

                rv.append(self._create_product(result))
                bindings_seen[result_binding] = True
            except Exception as e:
                print e
                continue
        return rv
