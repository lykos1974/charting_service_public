
$( document ).ready(function() {
    $('#center_column').on('scroll', function() {
        $('#left_column').scrollTop($(this).scrollTop());
        $('#right_column').scrollTop($(this).scrollTop());
        });


    $("#BuSL").click(function() {
        $(this).data('clicked', true);
        //alert("reer");
        });

    $("#BeSL").click(function(){
        $(this).data('clicked', true);

        });

    $("#BuTL").click(function(){
        $(this).data('clicked', true);

        });

    $("#BeTL").click(function(){
        $(this).data('clicked', true);

        });

    $("#DeleteLine").click(function(){
        $(this).data('clicked', true);

        });

    $("#Exchange").select2( {
         placeholder: "Select Exchange",
         allowClear: true
     } );


            // Code to hide elements
            document.getElementById( 'Drawing' ).style.display = 'none';
            document.getElementById( 'BuSL' ).style.display = 'none';
            document.getElementById( 'BeSL' ).style.display = 'none';
            document.getElementById( 'BuTL' ).style.display = 'none';
            document.getElementById( 'BeTL' ).style.display = 'none';
            document.getElementById( 'DeleteLine' ).style.display = 'none';



        });

        function rem(event)
            {
              if($("#DeleteLine").data('clicked')) {
                var linetoremove = event.target;
                var parent    = linetoremove.parentNode;
                parent.removeChild(linetoremove);
                $("#DeleteLine").data('clicked', false);
                }
            }


function init(exchange,pair,period){
    exchange = exchange.toLowerCase();;
    if(exchange == undefined){
        exchange = "_1btcxe";
    }

    $("#Currency_Pair").empty();
    $("#Time_Period").empty();

    $.ajax({
        url: "../getInfo/"+exchange,
    })
  .done(function( data ) {

      $.each(data.pairs, function(value) {
        if(data.pairs[value] == pair){
             $("#Currency_Pair").append('<option value="'+data.pairs[value]+'" selected="selected" >'+data.pairs[value]+'</option>');
        } else {
            $("#Currency_Pair").append('<option value="'+data.pairs[value]+'" >'+data.pairs[value]+'</option>');
        }

       });

       $.each(data.timeFrames, function(key) {
         if(key == period){
            $("#Time_Period").append('<option value="'+key+'" selected="selected" >'+key+'</option>');
        } else {
            $("#Time_Period").append('<option value="'+key+'" >'+key+'</option>');
        }
       });

        $("#Currency_Pair").select2( {
         placeholder: "Select Currency Pair",
         allowClear: true
       });

  });


width = $('#clickable').width();
var parentWidth = $('#clickable').offsetParent().width();
//alert("svg width:",$('#clickable').width());
// alert("parent div width:",parentWidth);
if (parentWidth > width){
   // alert("inside func");
    //$('#center_column').removeAttr('width')

    $('#center_column').css({ width: ""});
    //alert(width);alert(parentWidth);

    }else {
        $('#center_column').css({ width: "82%"});
     }


  }




            function loadSVG() {
                // Code to show elements
                document.getElementById( 'Drawing' ).style.display = 'inline-block';
                document.getElementById( 'BuSL' ).style.display = 'inline-block';
                document.getElementById( 'BeSL' ).style.display = 'inline-block';
                document.getElementById( 'BuTL' ).style.display = 'inline-block';
                document.getElementById( 'BeTL' ).style.display = 'inline-block';
                document.getElementById( 'DeleteLine' ).style.display = 'inline-block';


                $('#clickable').click(function(e) {

                    if($('#BuSL').data('clicked')) {
                        // Bullish support line creation
                        var offset_t = $(this).offset().top - $(window).scrollTop();
                        var offset_l = $(this).offset().left - $(window).scrollLeft();

                        var left = Math.round( (e.clientX - offset_l) );
                        var top = Math.round( (e.clientY - offset_t) );

                        //alert("Left: " + left + " Top: " + top);
                        var newLine = document.createElementNS('http://www.w3.org/2000/svg','line');
                        newLine.setAttribute('id','line2');
                        newLine.setAttribute('x1','0');
                        newLine.setAttribute('y1',top);
                        newLine.setAttribute('x2',$(this).width());
                        newLine.setAttribute('y2',top);
                        newLine.setAttribute('fill','black');
                        newLine.setAttribute('stroke','lightgreen');
                        newLine.setAttribute('stroke-width','3');
                        newLine.setAttribute('onclick','rem(evt)');
                        $("#clickable").append(newLine);
                        $('#BuSL').data('clicked', false);
                        $('#BeSL').data('clicked', false);
                        $('#BeTL').data('clicked', false);
                        $('#BuTL').data('clicked', false);
                        $("#DeleteLine").data('clicked', false);
                        }


                    if($('#BeSL').data('clicked')) {
                        // Bearish resistance line creation
                        var offset_t = $(this).offset().top - $(window).scrollTop();
                        var offset_l = $(this).offset().left - $(window).scrollLeft();

                        var left = Math.round( (e.clientX - offset_l) );
                        var top = Math.round( (e.clientY - offset_t) );

                        //alert("Left: " + left + " Top: " + top);
                        var newLine = document.createElementNS('http://www.w3.org/2000/svg','line');
                        newLine.setAttribute('id','line2');
                        newLine.setAttribute('x1','0');
                        newLine.setAttribute('y1',top);
                        newLine.setAttribute('x2',$(this).width());
                        newLine.setAttribute('y2',top);
                        newLine.setAttribute('fill','black');
                        newLine.setAttribute('stroke','orange');
                        newLine.setAttribute('stroke-width','3');
                        newLine.setAttribute('onclick','rem(evt)');
                        $("#clickable").append(newLine);
                        $('#BuSL').data('clicked', false);
                        $('#BeSL').data('clicked', false);
                        $('#BeTL').data('clicked', false);
                        $('#BuTL').data('clicked', false);
                        $("#DeleteLine").data('clicked', false);
                        }


                    if($('#BeTL').data('clicked')) {
                        // Bearish resistance trend line creation
                        var offset_t = $(this).offset().top - $(window).scrollTop();
                        var offset_l = $(this).offset().left - $(window).scrollLeft();

                        var left = Math.round( (e.clientX - offset_l) );
                        var top = Math.round( (e.clientY - offset_t) );
                        var tan = Math.round(top / Math.tan(45))

                        //alert("Left: " + left + " Top: " + top + " Tan: " + tan);
                        var newLine = document.createElementNS('http://www.w3.org/2000/svg','line');
                        newLine.setAttribute('id','line2');
                        newLine.setAttribute('x1',left);
                        newLine.setAttribute('y1',top);
                        newLine.setAttribute('x2',left+$(this).height());
                        newLine.setAttribute('y2',top+$(this).height());
                        newLine.setAttribute('fill','black');
                        newLine.setAttribute('stroke','orange');
                        newLine.setAttribute('stroke-width','3');
                        newLine.setAttribute('onclick','rem(evt)');
                        $("#clickable").append(newLine);
                        $('#BuSL').data('clicked', false);
                        $('#BeSL').data('clicked', false);
                        $('#BeTL').data('clicked', false);
                        $('#BuTL').data('clicked', false);
                        $("#DeleteLine").data('clicked', false);
                        }


                    if($('#BuTL').data('clicked')) {
                        // Bullish support trend line creation
                        var offset_t = $(this).offset().top - $(window).scrollTop();
                        var offset_l = $(this).offset().left - $(window).scrollLeft();

                        var left = Math.round( (e.clientX - offset_l) );
                        var top = Math.round( (e.clientY - offset_t) );
                        var tan = Math.round(top / Math.tan(45))

                        //alert("Left: " + left + " Top: " + top + " Tan: " + tan);
                        var newLine = document.createElementNS('http://www.w3.org/2000/svg','line');
                        newLine.setAttribute('id','line2');
                        newLine.setAttribute('x1',left);
                        newLine.setAttribute('y1',top);
                        newLine.setAttribute('x2',left+$(this).height());
                        newLine.setAttribute('y2',top-$(this).height());
                        newLine.setAttribute('fill','black');
                        newLine.setAttribute('stroke','lightgreen');
                        newLine.setAttribute('stroke-width','3');
                        newLine.setAttribute('onclick','rem(evt)');
                        $("#clickable").append(newLine);
                        $('#BuSL').data('clicked', false);
                        $('#BeSL').data('clicked', false);
                        $('#BeTL').data('clicked', false);
                        $('#BuTL').data('clicked', false);
                        $("#DeleteLine").data('clicked', false);
                        }
                });

            }
