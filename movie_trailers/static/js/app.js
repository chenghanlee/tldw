// "use strict";

var Trailer = function() {
    function reduceText(tag, maxLength){
        var minimized_elements = $(tag);
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
        reduceText: reduceText
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
		});
    }

    var _customRenderFunction = function(document_type, item) {
    	var title = item['title'],
            numCast = _.size(item['cast']),
            castOne = (numCast >= 1) ? item['cast'][0] : null,
            castTwo = (numCast >= 2) ? item['cast'][1] : null,
            castThree = (numCast >= 3) ? item['cast'][2] : null,
    		releaseYear = item['release_date'].split('-')[0];

    	var searchResult = searchResultTitle({'title': title, 'year': releaseYear});
        var searchSubResult = searchResultSubTitle({'castOne': castOne,
                                                     'castTwo': castTwo,
                                                     'castThree': castThree});
    	return searchResult.concat(searchSubResult);
	};

    return{
        autoComplete: autoComplete
    };
}();

$(document).ready(function() {    
    SwyftType.autoComplete();
    Trailer.reduceText("p#biography", 110);
    Trailer.reduceText("p#synopsis", 350);
});