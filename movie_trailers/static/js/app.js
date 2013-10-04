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
    	searchResultTitle = _.template("<p class='title'><%= title %> (<%= year %>)</p>");

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
    		releaseYear = item['release_date'].split('-')[0];

    	var searhResult = searchResultTitle({'title': title, 'year': releaseYear});
    	return searhResult;
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