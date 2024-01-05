if ($ === undefined) $ = CTFd.lib.$
$("#score-type").change(function(e) {
    if (e.target.value == '1') {
        $('#static-score').hide();
        $('#dynamic-score').show();
    } else {
        $('#dynamic-score').hide();
        $('#static-score').show();
    }
});
$("#score-type").change()