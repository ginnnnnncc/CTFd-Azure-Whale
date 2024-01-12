if ($ === undefined) $ = CTFd.lib.$
$("#score-type").change(function(e) {
    if (e.target.value == '1') {
        $('#static-score').hide();
        $('#dynamic-score').show();
        $('input[name=value]').attr('required', false);
        $('input[name=initial]').attr('required', true);
        $('input[name=decay]').attr('required', true).attr('min', 1);
        $('input[name=minimum]').attr('required', true);
    } else {
        $('#dynamic-score').hide();
        $('#static-score').show();
        $('input[name=value]').attr('required', true);
        $('input[name=initial]').attr('required', false);
        $('input[name=decay]').attr('required', false).attr('min', null);
        $('input[name=minimum]').attr('required', false);
    }
});
$("#score-type").change()