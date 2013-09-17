from amazonproduct.api import API
from lxml import etree

class AmazonProductSearch():
    def __init__(self, aws_access_key, aws_secret_key, affiliate_key):
        self.api = API(aws_access_key, aws_secret_key, 'us', affiliate_key)

    def _create_product(self, result):
        '''
        CHLEE TODO:
        Need to grab the price of the media sold by Amazon
        and not media sold by a third party, which is what i am
        currently grabbing
        '''

        product = {}
        product['ASIN'] = str(result.ASIN)
        product['Amount'] = str(result.OfferSummary.LowestNewPrice.Amount)
        product['Binding'] = str(result.ItemAttributes.Binding)
        product['DetailPageURL'] = str(result.DetailPageURL)
        return product

    def item_search(self, title, actor, expected_running_time,
            ResponseGroup='OfferFull, Medium'):
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

        bindings_seen = {"DVD": False, "Blu-ray": False,
                        "Amazon Instant Video": False}
        max_running_time_diff = 5
        rv = []

        for result in results:
            try:
                if all(bindings_seen.values()):
                    return rv
                if abs(expected_running_time - result.ItemAttributes.RunningTime
                    ) <= max_running_time_diff:
                    binding = result.ItemAttributes.Binding
                    if not bindings_seen.get(binding):
                        rv.append(self._create_product(result))
                        bindings_seen[binding] = True
            except Exception as e:
                print e
                continue
        return rv
