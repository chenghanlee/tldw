"use strict";

var infiniteScroll = function () {
    var thumbnail = ".thumbnail",
        thumbnailContainer = ".thumbnails",
        moreMovies = ".moreMovies";

    function appendMovie(movies) {
        console.log("appending movie");

        var container = $(thumbnailContainer),
            path = "/static/templates/thumbnail.handlebars";

        $.ajax({
            url: path,
            cache: true,
        })
        .done(function(data){
            var template = Handlebars.compile(data);
            $(thumbnailContainer).append(template(movies));
            console.log($(moreMovies).contents());
            $(moreMovies).contents().wrap("a");
        });
    }

    function getMoreMovies(postURL) {
        // TODO CHLEE:
        // 1) Clean up the variables needed
        // 2) Better logic than lastThumbnailIndex to determine which movies to load
        // 3) Memoize this function call using jstorage
        // 4) use getMoreMovie movies and append movies as deferred
        //    --> getMoreMovies(postURL).then(appendMovies);
        var deferred = new $.Deferred(),
            lastThumbnail = _.max($(thumbnail), function(eachThumbnail){
                var thumbnailIndex = $(eachThumbnail).attr("data-position");
                return _.parseInt(thumbnailIndex);
            }),
            lastThumbnailIndex = $(lastThumbnail).attr("data-position");

        $(moreMovies).find("a").contents().unwrap();
        $.ajax({
            url: postURL,
            data: {"index": lastThumbnailIndex},
            type: "POST"
        })
        .done(function(rv) {
            if(rv['status'] === "success"){
                deferred.resolve(rv['data']);
            }
            else{
                console.log(rv['msg']);
                deferred.reject();
            }
        })
        .fail(function() {
            deferred.reject();
        });

        return deferred.promise();
    }

    function loadMoreMovies() {
        $(moreMovies).click(function(e){
            e.preventDefault();

            var url =  window.location.pathname;
            getMoreMovies(url).done(appendMovie);
        });
    }

    return{
        loadMoreMovies: loadMoreMovies
    };
}();

// var trailerLinks = function () {
//     // private variables
//     var ulClass = ".trailer-links",
//         liClass = ".trailer",
//         currentTrailer = "current-trailer";

//     function getEmbeddedYoutubeID(trailerID, trailerURL) {
//         var deferred = new $.Deferred(),
//             key = trailerID + ":youtubeID",
//             youtubeID = $.jStorage.get(key, null);

//         // check to see if we cached the 
//         // youtubeID in local storage
//         if (youtubeID !== null ) {
//             deferred.resolve(trailerURL, youtubeID);
//         }
//         // if not, make an ajax post to trailerURL
//         // and the server will return the youtubeID
//         // which we can then pass to changeEmbeddedVideo
//         // and change the youtube video embedded in the page
//         else{
//             $.ajax({
//                 url: trailerURL,
//                 type: "POST"
//             })
//             .done(function(data) {
//                 youtubeID = data["youtubeID"];
//                 $.jStorage.set(key, youtubeID); //save youtube_id for future use
//                 deferred.resolve(trailerURL, youtubeID);
//             })
//             .fail(function() {
//                 deferred.reject();
//             });
//         }

//         return deferred.promise();
//     }

//     function changeEmbeddedVideo(trailerURL, youtubeID) {
//         var deferred = new $.Deferred(),
//             embedLink = "http://www.youtube.com/embed/" +
//                         youtubeID +
//                         "?rel=0&iv_load_policy=3&modestbranding=1",
//             title = document.getElementsByTagName("title")[0].innerHTML;

//         // updating the embedded youtube video to a different video
//         $("iframe").attr("src", embedLink);
        
//         // saving browser state so we ...
//         // var data = _createPageState($(ulClass).html(), youtubeID);
//         // History.replaceState(data, title, trailerURL);
//         deferred.resolve();

//         return deferred.promise();
//     }

//     function _createPageState(sidebarHTML, youtubeID){
//         var data = {
//             "type": "youtubeVideoChange",
//             "sideBar": sidebarHTML,
//             "youtubeID":  youtubeID
//         }

//         return data;
//     }
//     function addAnchorTag(){
//         // Loop through each li tag of the trailer links and
//         // find the trailer link that:
//         // 1) doesn't have an anchor tag and 
//         // 2) is not the current-trailer
//         _.forEach($(ulClass).children(), function(liElement){
//             var $element = $(liElement),
//                 noAnchorTag = $element.has("a").length === 0,
//                 isNotCurrentTrailer = !$element.hasClass("current-trailer");
            
//             if(noAnchorTag && isNotCurrentTrailer){
//                 var id = $element.attr("id"),
//                     key = id + ":href",
//                     url = $.jStorage.get(key, null);
                
//                 // if the url associated for this li tag is not cached
//                 // in jStorage, we have to manually re-recreate the
//                 // url ourselves
//                 if (url === null){
//                    url = _createUrl($element.index());
//                 }

//                 $element.contents()
//                         .wrap("<a class='trailer' href='" + url + "'></a>");
//             }
//         });
//     }

//     function _createUrl(trailerIndex) {
//         // If we are the associate URL for the li tag is not
//         // found in localStorage. We can re-create the URL through
//         // the heuristic below. 

//         var currentUrl = window.location.pathname,
//             lastChar = currentUrl.slice(-1),
//             secondToLastChar = currentUrl.slice(-2, -1),
//             index = trailerIndex+1,
//             url;

//         // example: http://127.0.0.1/Toy-Story/
//         if (lastChar === '/'){
//             url = currentUrl + index;
//         }
//         else{
//             // example: http://127.0.0.1/Toy-Story
//             if (isNaN(lastChar)) {
//                 url = currentUrl + '/' + index;
//             }
//             else{
//                 // example: http://127.0.0.1/Toy-Story/2
//                 if(secondToLastChar === '/') {
//                     url = currentUrl.substr(0, currentUrl.length-1) + index;
//                 }
//                 // example: http://127.0.0.1/Iron-Man-2
//                 else {
//                     url = currentUrl + '/' + index;
//                 }
//             }
//         }

//         return url;
//     }

//     function removeAnchorTag() {
//         var context = $(this),
//             deferred = new $.Deferred(),
//             id = context.parent().attr("id"),
//             key = id + ":href",
//             url = context.attr("href");

//         // save the URL of this trailer link's anchor tag
//         // in case we need to retrieve the URL later
//         $.jStorage.set(key, url);
       
//         // find the li tag that currently holds the
//         // current-trailer class and remove that class
//         // from that li tag because it is no longer 
//         // the "current trailer" link as we are 
//         // "navigating" to a new URL
//         $('.' + currentTrailer).removeAttr("class");

//         // add the current-trailer class to the link
//         // that we just clicked on. Also remove the 
//         // anchor tag that was embedded in it
//         // since we are simulating that we have navigated
//         // to that link via history.js and we want to
//         // show the user that they are "viewing" this link
//         var text = context.text();
//         context.parent()
//                .html(text)
//                .addClass(currentTrailer);

//         deferred.resolve();
//         return deferred.promise();
//     }

//     function listenToClick (){
//         $(ulClass).on("click", liClass, function (e) {
//             e.preventDefault();
            
//             var id = $(this).parent().attr("id"),
//                 url = $(this).attr("href");
            
//             getEmbeddedYoutubeID(id, url).then(changeEmbeddedVideo)
//                                          .then($.proxy(removeAnchorTag, $(this)))
//                                          .done(addAnchorTag);
//         });
//     }


//     // Reveal public pointers to 
//     // private functions and properties
//     return{
//         listenToClick: listenToClick
//     };
// }();

$(document).ready(function() {    
    // $.jStorage.flush();
    // trailerLinks.listenToClick();
    infiniteScroll.loadMoreMovies();
});