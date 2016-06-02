/*
* This file is part of INSPIRE.
* Copyright (C) 2015, 2016 CERN.
*
* INSPIRE is free software; you can redistribute it and/or
* modify it under the terms of the GNU General Public License as
* published by the Free Software Foundation; either version 2 of the
* License, or (at your option) any later version.
*
* INSPIRE is distributed in the hope that it will be useful, but
* WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
* General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with INSPIRE; if not, write to the Free Software Foundation, Inc.,
* 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
*/

 define(
  [
    'jquery',
    'flight',
    'datatables',
    'bootstrap'
  ],
  function($, flight) {
      'use strict';

      return flight.component(Datatables);

      function Datatables() {

        this.attributes({
          recid: '',
          collection: '',
          citation_count: ''
        });

        this.after('initialize', function() {
          var that = this;

          $('#record-references-table').DataTable({
            language: {
              info: "Showing _START_ to _END_ of _TOTAL_ references",
              search: "_INPUT_",
              searchPlaceholder: "Filter references..."
            },
            "ajax": {
              "url": "/ajax/references",
              "data": {
                recid: that.attr.recid,
                collection: that.attr.collection
              },
              "method": "GET"
            },
            "fnInitComplete": function(oSettings, json) {
              if ( json.data.length > 0 ) {
                $("#record-references-loading").hide();
                $('#record-references-table-wrapper').show();
              }
              else {
                $('#references .panel-body').text("There are no references available for this record.").show()
              }
            },
            "aaSorting": [],
            "autoWidth": false
          });

          $('#record-citations-table').DataTable({
            language: {
              info: "Showing _START_ to _END_ of " + that.attr.citation_count + " citations"
            },
            "bPaginate": false,
            "ajax": {
              "url": "/ajax/citations",
              "data": {
                recid: that.attr.recid,
                collection: that.attr.collection
              },
              "method": "GET"
            },
            "fnInitComplete": function(oSettings, json) {
              if ( json.data.length > 0 ) {
                $("#record-citations-loading").hide();
                $('#record-citations-table-wrapper').show();
              }
              else {
                $('#citations .panel-body').text("There are no citations available for this record.").show()
              }
            },
            "aaSorting": [],
            "autoWidth": false,
            "paging": false,
            "searching": false
          });

          $('#record-institution-people-table').DataTable({
            "bLengthChange": false,
            "bInfo" : false,
            "ajax": {
              "url": "/ajax/institutions/people",
              "data": {
                recid: that.attr.recid
              },
              "method": "GET"
            },
            "fnInitComplete": function(oSettings, json) {
              if ( json.data.length > 0 ) {
                $("#record-institution-people-loading").hide();
                $("#record-institution-people-table-wrapper ul.pagination").addClass("pagination-sm");
                var total_text = json.data.length + " Authors ";
                $("#record-institution-people .panel-heading").html(total_text);
                $('#record-institution-people-table-wrapper').show();
              }
              else {
                $('#record-institution-people .panel-body').text("There are no authors on INSPIRE associated with this institution.").show()
              }
            },
            "aaSorting": [],
            "autoWidth": false,
            // "paging": false,
            "searching": false,
            dom:
              "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
              "<'row'<'col-sm-12'tr>>" +
              "<'row'<'col-sm-12'p>>"
          });

          $('#record-institution-experiments-table').DataTable({
            "bLengthChange": false,
            "bInfo" : false,
            "ajax": {
              "url": "/ajax/institutions/experiments",
              "data": {
                recid: that.attr.recid
              },
              "method": "GET"
            },
            "fnInitComplete": function(oSettings, json) {
              if ( json.data.length > 0 ) {
                $("#record-institution-experiments-loading").hide();
                $("#record-institution-experiments-table-wrapper ul.pagination").addClass("pagination-sm");
                var total_text = json.total + " Experiments ";
                if ( json.total > json.data.length ) {
                  total_text = total_text + "<span class='record-panel-heading-muted'> Showing newest " + json.data.length + "</span>";
                }
                $("#record-institution-experiments .panel-heading").html(total_text);
                $('#record-institution-experiments-table-wrapper').show();
              }
              else {
                $('#record-institution-experiments .panel-body').text("There are no experiments on INSPIRE associated with this institution.").show()
              }
            },
            "aaSorting": [[1, 'desc']],
            "autoWidth": false,
            // "paging": false,
            "searching": false,
            dom:
              "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
              "<'row'<'col-sm-12'tr>>" +
              "<'row'<'col-sm-12'p>>"
          });

          $('#record-institution-papers-table').DataTable({
            "bLengthChange": false,
            "bInfo" : false,
            "ajax": {
              "url": "/ajax/institutions/papers",
              "data": {
                recid: that.attr.recid
              },
              "method": "GET"
            },
            "fnInitComplete": function(oSettings, json) {
              if ( json.data.length > 0 ) {
                $("#record-institution-papers-loading").hide();
                $("#record-institution-papers-table-wrapper ul.pagination").addClass("pagination-sm");
                var total_text = json.total + " Papers ";
                if ( json.total > json.data.length ) {
                  total_text = total_text + "<span class='record-panel-heading-muted'> Showing newest " + json.data.length + "</span>";
                }
                $("#record-institution-papers .panel-heading").html(total_text);
                $('#record-institution-papers-table-wrapper').show();
              }
              else {
                $('#record-institution-papers .panel-body').text("There are no papers on INSPIRE associated with this institution.").show()
              }
            },
            "aaSorting": [],
            "aoColumns": [
            { sWidth: '50%' },
            { sWidth: '20%' },
            { sWidth: '10%' },
            { sWidth: '10%' },
            { sWidth: '10%' }],
            "autoWidth": false,
            // "paging": false,
            "searching": false,
            dom:
              "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
              "<'row'<'col-sm-12'tr>>" +
              "<'row'<'col-sm-12'p>>"
          });

          $('#record-institution-phdtheses-table').DataTable({
            "bLengthChange": false,
            "bInfo" : false,
            "ajax": {
              "url": "/ajax/institutions/phdtheses",
              "data": {
                recid: that.attr.recid
              },
              "method": "GET"
            },
            "fnInitComplete": function(oSettings, json) {
              if ( json.data.length > 0 ) {
                $("#record-institution-phdtheses-loading").hide();
                $("#record-institution-phdtheses-table-wrapper ul.pagination").addClass("pagination-sm");
                $("#record-institution-phdtheses .panel-heading").text(json.data.length + " PhD Theses")
                $('#record-institution-phdtheses-table-wrapper').show();
              }
              else {
                $('#record-institution-phdtheses .panel-body').text("There are no PhD Theses on INSPIRE associated with this institution.").show()
              }
            },
            "aaSorting": [[4, 'desc']],
            "aoColumns": [
            { sWidth: '50%' },
            { sWidth: '20%' },
            { sWidth: '10%' },
            { sWidth: '10%' },
            { sWidth: '10%' }],
            "autoWidth": false,
            // "paging": false,
            "searching": false,
            dom:
              "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
              "<'row'<'col-sm-12'tr>>" +
              "<'row'<'col-sm-12'p>>"
          });
      });

    }

});
