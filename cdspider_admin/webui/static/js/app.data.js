$(document).ready(function() {

	 $('#docs pre code').each(function(){
	    var $this = $(this);
	    var t = $this.html();
	    $this.html(t.replace(/</g, '&lt;').replace(/>/g, '&gt;'));
	});

	function getRandomInt(min, max) {
	  return Math.floor(Math.random() * (max - min + 1)) + min;
	};

	$(document).on('click', '.the-icons a', function(e){
		e && e.preventDefault();
	});

	$(document).on('change', 'table thead [type="checkbox"]', function(e){
		e && e.preventDefault();
		var $table = $(e.target).closest('table'), $checked = $(e.target).is(':checked');
		$('tbody [type="checkbox"]',$table).attr('checked', $checked);
	});

	$(document).on('click', '[data-toggle^="progress"]', function(e){
		e && e.preventDefault();

		$el = $(e.target);
		$target = $($el.data('target'));
		$('.progress', $target).each(
			function(){
				var $max = 50, $data, $ps = $('.progress-bar',this).last();
				($(this).hasClass('progress-mini') || $(this).hasClass('progress-small')) && ($max = 100);
				$data = Math.floor(Math.random()*$max)+'%';
				$ps.css('width', $data).attr('data-original-title', $data);
			}
		);
	});

	function addNotification($notes){
		var $el = $('#panel-notifications'), $n = $('.count-n:first', $el), $item = $('.list-group-item:first', $el).clone(), $v = parseInt($n.text());
		$('.count-n', $el).fadeOut().fadeIn().text($v+1);
		$item.attr('href', $notes.link);
		$item.find('.pull-left').html($notes.icon);
		$item.find('.media-body').html($notes.title);
		$item.hide().prependTo($el.find('.list-group')).slideDown().css('display','block');
	}
	var $noteMail = {
		icon: '<i class="icon-envelope-alt icon-2x text-default"></i>',
		title: 'Added the mail app, Check it out.<br><small class="text-muted">2 July 13</small>',
		link: 'mail.html'
	}
	var $noteCalendar = {
		icon: '<i class="icon-calendar icon-2x text-default"></i>',
		title: 'Added the calendar, Get it.<br><small class="text-muted">10 July 13</small>',
		link: 'calendar.html'
	}
	var $noteTimeline = {
		icon: '<i class="icon-time icon-2x text-default"></i>',
		title: 'Added the timeline, view it here.<br><small class="text-muted">1 minute ago</small>',
		link: 'timeline.html'
	}
	window.setTimeout(function(){addNotification($noteMail)}, 2000);
	window.setTimeout(function(){addNotification($noteCalendar)}, 3500);
	window.setTimeout(function(){addNotification($noteTimeline)}, 5000);

	// fullcalendar
	var date = new Date();
	var d = date.getDate();
	var m = date.getMonth();
	var y = date.getFullYear();
	var addDragEvent = function($this){
		// create an Event Object (http://arshaw.com/fullcalendar/docs/event_data/Event_Object/)
		// it doesn't need to have a start or end
		var eventObject = {
			title: $.trim($this.text()), // use the element's text as the event title
			className: $this.attr('class').replace('label','')
		};

		// store the Event Object in the DOM element so we can get to it later
		$this.data('eventObject', eventObject);

		// make the event draggable using jQuery UI
		$this.draggable({
			zIndex: 999,
			revert: true,      // will cause the event to go back to its
			revertDuration: 0  //  original position after the drag
		});
	};
	$('.calendar').each(function() {
		$(this).fullCalendar({
			header: {
				left: 'prev,next today',
				center: 'title',
				right: 'month,agendaWeek,agendaDay'
			},
			editable: true,
			droppable: true, // this allows things to be dropped onto the calendar !!!
			drop: function(date, allDay) { // this function is called when something is dropped

					// retrieve the dropped element's stored Event Object
					var originalEventObject = $(this).data('eventObject');

					// we need to copy it, so that multiple events don't have a reference to the same object
					var copiedEventObject = $.extend({}, originalEventObject);

					// assign it the date that was reported
					copiedEventObject.start = date;
					copiedEventObject.allDay = allDay;

					// render the event on the calendar
					// the last `true` argument determines if the event "sticks" (http://arshaw.com/fullcalendar/docs/event_rendering/renderEvent/)
					$('#calendar').fullCalendar('renderEvent', copiedEventObject, true);

					// is the "remove after drop" checkbox checked?
					if ($('#drop-remove').is(':checked')) {
						// if so, remove the element from the "Draggable Events" list
						$(this).remove();
					}

				}
			,
			events: [
				{
					title: 'All Day Event',
					start: new Date(y, m, 1)
				},
				{
					title: 'Long Event',
					start: new Date(y, m, d-5),
					end: new Date(y, m, d-2),
					className:'bg-primary'
				},
				{
					id: 999,
					title: 'Repeating Event',
					start: new Date(y, m, d-3, 16, 0),
					allDay: false
				},
				{
					id: 999,
					title: 'Repeating Event',
					start: new Date(y, m, d+4, 16, 0),
					allDay: false
				},
				{
					title: 'Meeting',
					start: new Date(y, m, d, 10, 30),
					allDay: false
				},
				{
					title: 'Lunch',
					start: new Date(y, m, d, 12, 0),
					end: new Date(y, m, d, 14, 0),
					allDay: false
				},
				{
					title: 'Birthday Party',
					start: new Date(y, m, d+1, 19, 0),
					end: new Date(y, m, d+1, 22, 30),
					allDay: false
				},
				{
					title: 'Click for Google',
					start: new Date(y, m, 28),
					end: new Date(y, m, 29),
					url: 'http://google.com/'
				}
			]
		});
	});
	$('#myEvents').on('change', function(e, item){
		addDragEvent($(item));
	});

	$('#myEvents li').each(function() {
		addDragEvent($(this));
	});

	// fuelux datagrid
	var DataGridDataSource = function (options) {
		this._formatter = options.formatter;
		this._columns = options.columns;
		this._delay = options.delay;
	};

	DataGridDataSource.prototype = {

		columns: function () {
			return this._columns;
		},

		data: function (options, callback) {
			var url = 'js/data/datagrid.json';
			var self = this;

			setTimeout(function () {

				var data = $.extend(true, [], self._data);

				$.ajax(url, {
					dataType: 'json',
					async: false,
					type: 'GET'
				}).done(function (response) {

					data = response.geonames;
					// SEARCHING
					if (options.search) {
						data = _.filter(data, function (item) {
							var match = false;

							_.each(item, function (prop) {
								if (_.isString(prop) || _.isFinite(prop)) {
									if (prop.toString().toLowerCase().indexOf(options.search.toLowerCase()) !== -1) match = true;
								}
							});

							return match;
						});
					}

					// FILTERING
					if (options.filter) {
						data = _.filter(data, function (item) {
							switch(options.filter.value) {
								case 'lt5m':
									if(item.population < 5000000) return true;
									break;
								case 'gte5m':
									if(item.population >= 5000000) return true;
									break;
								default:
									return true;
									break;
							}
						});
					}

					var count = data.length;

					// SORTING
					if (options.sortProperty) {
						data = _.sortBy(data, options.sortProperty);
						if (options.sortDirection === 'desc') data.reverse();
					}

					// PAGING
					var startIndex = options.pageIndex * options.pageSize;
					var endIndex = startIndex + options.pageSize;
					var end = (endIndex > count) ? count : endIndex;
					var pages = Math.ceil(count / options.pageSize);
					var page = options.pageIndex + 1;
					var start = startIndex + 1;

					data = data.slice(startIndex, endIndex);

					if (self._formatter) self._formatter(data);

					callback({ data: data, start: start, end: end, count: count, pages: pages, page: page });
				}).fail(function(e){

				});
			}, self._delay);
		}
	};

    $('#MyStretchGrid').each(function() {
    	$(this).datagrid({
	        dataSource: new DataGridDataSource({
			    // Column definitions for Datagrid
			    columns: [
					{
						property: 'toponymName',
						label: 'Name',
						sortable: true
					},
					{
						property: 'countrycode',
						label: 'Country',
						sortable: true
					},
					{
						property: 'population',
						label: 'Population',
						sortable: true
					},
					{
						property: 'fcodeName',
						label: 'Type',
						sortable: true
					},
					{
						property: 'geonameId',
						label: 'Edit',
						sortable: true
					}
				],

			    // Create IMG tag for each returned image
			    formatter: function (items) {
			      $.each(items, function (index, item) {
			        item.geonameId = '<a href="#edit?geonameid='+item.geonameId+'"><i class="icon-pencil"></i></a>';
			      });
			    }
		  })
	    });
	});

	// datatable
	$('[data-ride="datatables"]').each(function() {
		var oTable = $(this).dataTable( {
			"bProcessing": true,
			"sAjaxSource": "js/data/datatable.json",
			"sDom": "<'row'<'col col-lg-6'l><'col col-lg-6'f>r>t<'row'<'col col-lg-6'i><'col col-lg-6'p>>",
			"sPaginationType": "full_numbers",
			"aoColumns": [
				{ "mData": "engine" },
				{ "mData": "browser" },
				{ "mData": "platform" },
				{ "mData": "version" },
				{ "mData": "grade" }
			]
		} );
	});

        $(document).on('click', '[data-ride="add-parse-rule"]', function(e){
            var $input = $(e.target).parents('.input-group').find(':input')
            var $target = $($(e.target).data('target'))
            var $column = $(e.target).data('column');
            var _v = $input.val()
            if (_v) {
                var pre_custom_columns = _v.split("\n")
                var _html = '';
                for (var idx in pre_custom_columns) {
                    var item = pre_custom_columns[idx];
                    var s = item.split("|");
                    var k = s[0];
                    var v = s[1] ? s[1] : '自定义字段';
                    _html += '<div class="form-group" id="'+ $column +'-column-'+ k +'">'+
                            '<label class="col-lg-2 control-label">'+ v +'识别规则</label>'+
                            '<div class="col-lg-9 input-group dropdown combobox m-b">'+
                                '<div class="input-group-btn">'+
                                     '<button type="button" class="btn btn-small btn-white dropdown-toggle" data-toggle="dropdown"><i class="caret"></i></button>'+
                                     '<ul class="dropdown-menu pull-right">'+
                                         '<li data-value="@value:"><a href="#">固定值</a></li>'+
                                         '<li data-value="@xpath:"><a href="#">XPATH选择器</a></li>'+
                                         '<li data-value="@css:"><a href="#">CSS选择器</a></li>'+
                                         '<li data-value="@reg:"><a href="#">正则表达式</a></li>'+
                                         '<li data-value="@json:"><a href="#">JSON表达式</a></li>'+
                                     '</ul>'+
                                '</div>'+
                                '<input type="text" name="'+ $column +'-'+ k +'" placeholder="" class="form-control" />'+
                                '<input type="hidden" name="'+ $column +'-name-'+ k +'" value="'+ v +'" />'+
                                '<span class="input-group-btn"><a href="#'+ $column +'-column-'+ k +'" data-dismiss="alert" class="btn btn-white btn-mini"><i class="icon-trash text-muted"></i>删除</a></span>'+
                            '</div>'+
                            '<label class="col-lg-2 control-label">'+ v +'提取规则</label>'+
                            '<div class="col-lg-9 input-group">'+
                                '<input type="text" name="'+ $column +'-'+ k +'-extract" placeholder="" class="form-control" />'+
                            '</div>'+
                        '</div>';
                }
                $target.append(_html)
            }
            else {
                alert("请添加自定义解析字段")
            }
	});

});
