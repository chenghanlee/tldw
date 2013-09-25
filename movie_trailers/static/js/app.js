// "use strict";

var Trailer = function() {
    var synopsis = "p#synopsis";

    function reduceSynopsis(maxLength){
        var minimized_elements = $(synopsis);
        minimized_elements.each(function(){    
            var t = $(this).text();        
            if(t.length < maxLength)
                return;
            
            $(this).html(
                t.slice(0, maxLength)+'<span> ... </span><a href="#" class="more">More</a>'+
                '<span style="display:none;">'+ t.slice(maxLength, t.length)+' <a href="#" class="less">Less</a></span>'
            );
            
        }); 
        
        $('a.more', minimized_elements).click(function(event){
            event.preventDefault();
            $(this).hide().prev().hide();
            $(this).next().show();        
        });
        
        $('a.less', minimized_elements).click(function(event){
            event.preventDefault();
            $(this).parent().hide().prev().show().prev().show();    
        });

    }

    return{
        reduceSynopsis: reduceSynopsis
    };
}();

var SwyftType = function () {
    // private variables
    var numResults = 8,
    	engineKey = "TqkNebr4pzvBxHTe7p6A",
    	searchBox = "#st-search-input",
    	searchResultTitle = _.template("<p class='title'><%= title %> (<%= year %>)</p>"),
		searchResultSubTitle = _.template("<p class='sub-title'><%= castOne %> &middot; <%= castTwo %> &middot; <%= castThree %></p>");

    function autoComplete() {
		$(searchBox).swiftype({ 
  			engineKey: engineKey,
  			resultLimit: numResults,
  			renderFunction: _customRenderFunction,
  			fetchFields: {'trailer': ['title', 'cast','release_date', 'url']},
    		searchFields: {'trailer': ['title']}
    		// sortField: {'trailer': 'release_date'},
      //     	sortDirection: {'books': 'asc'}
		});
    }

    var _customRenderFunction = function(document_type, item) {
    	var title = item['title'],
    		releaseYear = item['release_date'].split('-')[0],
    		numCast = _.size(item['cast']),
    		castOne = (numCast >= 1) ? item['cast'][0] : null,
    		castTwo = (numCast >= 2) ? item['cast'][1] : null,
    		castThree = (numCast >= 3) ? item['cast'][2] : null;

    	var title = searchResultTitle({'title': title, 'year': releaseYear});
    	var subTitle = searchResultSubTitle({'castOne': castOne,
    										 'castTwo': castTwo,
    										 'castThree': castThree});
    	return title.concat(subTitle);
	};

    return{
        autoComplete: autoComplete
    };
}();

$(document).ready(function() {    
    SwyftType.autoComplete();
    Trailer.reduceSynopsis(350);
});