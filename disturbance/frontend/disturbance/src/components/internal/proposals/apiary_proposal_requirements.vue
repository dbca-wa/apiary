<template id="proposal_requirements">
    <div class="col-md-12">
        <div class="row">
            <div class="card card">
                <div class="card-header">
                    <h3 class="card-title">Requirements
                        <a class="panelClicker" :href="'#'+panelBody" data-bs-toggle="collapse"  data-parent="#userInfo" expanded="false" :aria-controls="panelBody">
                            <span class="fa fa-chevron-down float-end "></span>
                        </a>
                    </h3>
                </div>
                <div class="card-body card-body collapse collapse show" :id="panelBody">
                    <form class="form-horizontal" action="index.html" method="post">
                        <div class="col-sm-12">
                            <button v-if="hasAssessorMode || hasReferralMode" @click.prevent="addRequirement()" style="margin-bottom:10px;" class="btn btn-primary float-end">Add Requirement</button>
                        </div>
                        <datatable ref="requirements_datatable" :id="'requirements-datatable-'+_uid" :dtOptions="requirement_options" :dtHeaders="requirement_headers"/>
                    </form>
                </div>
            </div>
        </div>
        <RequirementDetail ref="requirement_detail" :proposal_id="proposal.id" :requirements="requirements" :hasReferralMode="hasReferralMode" :referral_group="referral_group"/>
    </div>
</template>
<script>
import { v4 as uuid } from 'uuid';
import {
    api_endpoints,
    helpers,
    constants
}
from '@/utils/hooks'
import datatable from '@vue-utils/datatable.vue'
import RequirementDetail from './apiary_proposal_add_requirement.vue'
import $ from 'jquery';

export default {
    name: 'ApiaryProposalRequirements',
    props: {
        proposal: Object,
        hasReferralMode:{
            type:Boolean,
            default: false
        },
        referral_group:{
            type:Number,
            default: null
        }
    },
    data: function() {
        let vm = this;
        return {
            panelBody: "proposal-requirements-"+uuid(),
            requirements: [],
            requirement_headers:["Requirement","Due Date","Recurrence","Action","Order","Documents"],
            requirement_options:{
                autoWidth: false,
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                ajax: {
                    "url": helpers.add_endpoint_json(api_endpoints.proposals,vm.proposal.id+'/requirements'),
                    "dataSrc": ''
                },
                order: [],
                dom: "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                // buttons:[
                // 'excel', 'csv', ], //'copy'
                buttons:[
                {
                    extend: 'excelHtml5',
                    className: 'btn btn-primary me-2 rounded',
                    text:"Excel",
                    exportOptions:{
                        orthogonal:'export'
                    }
                },
                {
                    extend: 'csvHTML5',
                    className: 'btn btn-primary me-2 rounded',
                    text:"CSV",
                    exportOptions:{
                        orthogonal:'export'
                    }
                }
                ], //'copy'
                columnDefs: [
                    { responsivePriority: 1, targets: 0 }, // First visible column has top priority (e.g. proposal_number
                    { responsivePriority: 2, targets: -1 }, // If the actions is the last entry in columns then this will make it 2nd top priority soo as long as the screen is a decent size it will always be shown
                ],
                columns: [
                    {
                        data: "requirement",
                        //orderable: false,
                        'render': function (value, type) {
                            var ellipsis = '...',
                                truncated = _.truncate(value, {
                                    length: 25,
                                    omission: ellipsis,
                                    separator: ' '
                                }),
                                result = '<span>' + truncated + '</span>',
                                popTemplate = _.template('<a href="#" ' +
                                    'role="button" ' +
                                    'data-bs-toggle="popover" ' +
                                    'data-trigger="click" ' +
                                    'data-bs-placement="top auto"' +
                                    'data-html="true" ' +
                                    'data-content="<%= text %>" ' +
                                    '>more</a>');
                            if (_.endsWith(truncated, ellipsis)) {
                                result += popTemplate({
                                    text: value
                                });
                            }

                            //return result;
                            return type=='export' ? value : result;
                        },
                        'createdCell': helpers.dtPopoverCellFn,
                        defaultContent: '',
                    },
                    {
                        data: "due_date",
                        mRender:function (data) {
                            return data != '' && data != null ? moment(data).format('DD/MM/YYYY'): '';
                        },
                        orderable: false,
                        defaultContent: '',
                    },
                    {
                        data: "recurrence",
                        mRender:function (data,type,full) {
                            if (full.recurrence){
                                switch(full.recurrence_pattern){
                                    case 1:
                                        return `Once per ${full.recurrence_schedule} week(s)`;
                                    case 2:
                                        return `Once per ${full.recurrence_schedule} month(s)`;
                                    case 3:
                                        return `Once per ${full.recurrence_schedule} year(s)`;
                                    default:
                                        return '';
                                }
                            }
                            return '';
                        },
                        orderable: false,
                        defaultContent: '',
                    },
                    {
                        mRender:function (data,type,full) {
                            let links = '';
                            if (vm.proposal.assessor_mode.has_assessor_mode){
                                if(full.copied_from==null)
                                {
                                    links +=  `<a href='#' class="editRequirement" data-id="${full.id}">Edit</a><br/>`;
                                }
                                //links +=  `<a href='#' class="editRequirement" data-id="${full.id}">Edit</a><br/>`;
                                links +=  `<a href='#' class="deleteRequirement" data-id="${full.id}">Delete</a><br/>`;
                            }
                            else{
                                if(vm.hasReferralMode && full.can_referral_edit){
                                    if(full.copied_from==null)
                                {
                                    links +=  `<a href='#' class="editRequirement" data-id="${full.id}">Edit</a><br/>`;
                                }
                                //links +=  `<a href='#' class="editRequirement" data-id="${full.id}">Edit</a><br/>`;
                                links +=  `<a href='#' class="deleteRequirement" data-id="${full.id}">Delete</a><br/>`;
                                }
                            }
                            return links;
                        },
                        orderable: false,
                        defaultContent: '',
                    },
                    {
                        mRender:function (data,type,full) {
                            let links = '';
                            if (vm.proposal.assessor_mode.has_assessor_mode){
                                links +=  `<a class="dtMoveUp" data-id="${full.id}" href='#'><i class="fa fa-angle-up fa-2x"></i></a><br/>`;
                                links +=  `<a class="dtMoveDown" data-id="${full.id}" href='#'><i class="fa fa-angle-down fa-2x"></i></a><br/>`;
                            }
                            else{
                                if(vm.hasReferralMode && full.can_referral_edit){
                                    links +=  `<a class="dtMoveUp" data-id="${full.id}" href='#'><i class="fa fa-angle-up fa-2x"></i></a><br/>`;
                                    links +=  `<a class="dtMoveDown" data-id="${full.id}" href='#'><i class="fa fa-angle-down fa-2x"></i></a><br/>`;
                                }
                            }
                            return links;
                        },
                        orderable: false,
                        defaultContent: '',
                    },
                    {
                        data: 'requirement_documents',
                        mRender:function (data) {
                            let links = '';
                            _.forEach(data, function (doc) {
                                links += '<a href="' + doc._file + '" target="_blank"><p>' + doc.name+ '</p></a><br>';
                            });
                            return links;
                        },
                        defaultContent: '',
                    },

                ],
                processing: true,
                drawCallback: function () {
                    if (
                        vm.$refs.requirements_datatable &&
                        vm.$refs.requirements_datatable.table
                    ) {                    
                        $(vm.$refs.requirements_datatable.table).find('tr:last .dtMoveDown').remove();
                        $(vm.$refs.requirements_datatable.table).children('tbody').find('tr:first .dtMoveUp').remove();
                    }

                    // Remove previous binding before adding it
                    $('.dtMoveUp').unbind('click');
                    $('.dtMoveDown').unbind('click');

                    // Bind clicks to functions
                    $('.dtMoveUp').click(vm.moveUp);
                    $('.dtMoveDown').click(vm.moveDown);
                }
            }
        }
    },
    watch:{
        hasAssessorMode(){
            // reload the table
            this.updatedRequirements();
        }

    },
    components:{
        datatable,
        RequirementDetail
    },
    computed:{
        hasAssessorMode(){
            return this.proposal.assessor_mode.has_assessor_mode;
        },

    },
    methods:{
        addRequirement(){
            this.$refs.requirement_detail.requirement.referral_group=this.referral_group
            this.$refs.requirement_detail.isModalOpen = true;
        },
        removeRequirement(_id){
            let vm = this;
            swal.fire({
                title: "Remove Requirement",
                text: "Are you sure you want to remove this requirement?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Remove Requirement',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
            }).then((swalresult) => {
                if(swalresult.isConfirmed) {
                    
                    fetch(helpers.add_endpoint_json(api_endpoints.proposal_requirements,_id+'/discard'))
                    .then(async (response) => {
                        if (!response.ok) { return response.json().then(err => { throw err }); }
                        vm.$refs.requirements_datatable.vmDataTable.ajax.reload();
                    }).catch((error) => {
                        console.log(error);
                    });
                }
            },(error) => {
                console.log(error); 
            });
        },
        fetchRequirements(){
            let vm = this;
            
            fetch(api_endpoints.proposal_standard_requirements).then(
                async (response) => {
                    if (!response.ok) { return response.json().then(err => { throw err }); }
                    vm.requirements = await response.json();
                }).catch((error) => {
                    console.log(error);
                });
        },
        editRequirement(_id){
            fetch(helpers.add_endpoint_json(api_endpoints.proposal_requirements,_id))
            .then(async (response) => {
                if (!response.ok) { return response.json().then(err => { throw err }); }
                const data = await response.json();
                this.$refs.requirement_detail.requirement = data;
                this.$refs.requirement_detail.requirement.due_date =  data.due_date != null && data.due_date != undefined ? moment(data.due_date).format('DD/MM/YYYY'): '';
                this.$refs.requirement_detail.requirement.referral_group=data.referral_group;
                this.$refs.requirement_detail.requirement.requirement_documents=data.requirement_documents;
                data.standard ? $(this.$refs.requirement_detail.$refs.standard_req).val(data.standard_requirement).trigger('change'): '';
                this.addRequirement();
             }).catch((error) => {
                console.log(error);
            })
        },
        updatedRequirements(){
            this.$refs.requirements_datatable.vmDataTable.ajax.reload();
        },
        eventListeners(){
            let vm = this;
            vm.$refs.requirements_datatable.vmDataTable.on('click', '.deleteRequirement', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.removeRequirement(id);
            });
            vm.$refs.requirements_datatable.vmDataTable.on('click', '.editRequirement', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.editRequirement(id);
            });
        },
        sendDirection(req,direction){
            let movement = direction == 'down'? 'move_down': 'move_up';
            fetch(helpers.add_endpoint_json(api_endpoints.proposal_requirements,req+'/'+movement)).then(() => {
            },(error) => {
                console.log(error);
                
            })
        },
        moveUp(e) {
            // Move the row up
            let vm = this;
            e.preventDefault();
            var tr = $(e.target).parents('tr');
            vm.moveRow(tr, 'up');
            vm.sendDirection($(e.target).parent().data('id'),'up');
        },
        moveDown(e) {
            // Move the row down
            e.preventDefault();
            let vm = this;
            var tr = $(e.target).parents('tr');
            vm.moveRow(tr, 'down');
            vm.sendDirection($(e.target).parent().data('id'),'down');
        },
        moveRow(row, direction) {
            // Move up or down (depending...)
            var table = this.$refs.requirements_datatable.vmDataTable;
            var index = table.row(row).index();

            var order = -1;
            if (direction === 'down') {
              order = 1;
            }

            var data1 = table.row(index).data();
            data1.order += order;

            var data2 = table.row(index + order).data();
            data2.order += -order;

            table.row(index).data(data2);
            table.row(index + order).data(data1);

            table.page(0).draw(false);
        }
    },
    mounted: function(){
        let vm = this;
        this.fetchRequirements();
        vm.$nextTick(() => {
            this.eventListeners();
        });
    }
}
</script>
<style scoped>
.dataTables_wrapper .dt-buttons{
    float: right;
}
</style>
