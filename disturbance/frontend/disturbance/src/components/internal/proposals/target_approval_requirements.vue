<template id="proposal_requirements">
    <FormSection :formCollapse="false" :label="sectionTitle" Index="requirements">
        <form class="form-horizontal" action="index.html" method="post">
            <div class="row">
                <div class="col-sm-12">
                    <button v-if="hasAssessorMode" @click.prevent="addRequirement()" style="margin-bottom:10px;" class="btn btn-primary float-end">Add Requirement</button>
                </div>
            </div>
            <datatable ref="target_requirements_datatable" :id="datatable_id" :dtOptions="requirement_options" :dtHeaders="requirement_headers"/>
        </form>
    </FormSection>
    <RequirementDetail ref="target_requirement_detail" :proposal_id="proposal.id" :requirements="requirements" :sitetransfer_approval_id="targetApprovalId"/>
</template>
<script>
import { v4 as uuidv4 } from 'uuid';
import {
    api_endpoints,
    helpers,
    constants
}
from '@/utils/hooks'
import datatable from '@vue-utils/datatable.vue'
import RequirementDetail from './proposal_add_requirement.vue'
import FormSection from "@/components/forms/section_toggle.vue";
import $ from 'jquery';

export default {
    name: 'TargetApprovalRequirements',
    props: {
        proposal: Object,
        targetApprovalId: Number,
        targetApprovalLodgementNumber: String,
    },
    data: function() {
        let vm = this;
        return {
            panelBody: "proposal-requirements-"+uuidv4(),
            datatable_id: 'target-approval-requirements-datatable-'+uuidv4(),
            //targetApproval: {},
            requirements: [],
            requirement_headers:[
                "Requirement",
                "Due Date",
                "Recurrence",
                "Action",
                "Order"
            ],
            // keyVersion: 0,
            requirement_options:{
                autoWidth: false,
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                ajax: {
                    "url": helpers.add_endpoint_json(api_endpoints.proposals,vm.proposal.id+'/apiary_site_transfer_target_approval_requirements'),
                    "dataSrc": ''
                },
                order: [],
                dom: "<'d-flex align-items-center'<'me-auto'l>fB>" +
                    "<'row'<'col-sm-12'tr>>" +
                    "<'d-flex align-items-center'<'me-auto'i>p>",
                buttons:[
                    {
                        extend: 'excel',
                        className: 'btn btn-primary me-2 rounded',
                        exportOptions: {
                            columns: ':not(.noexport)',
                            orthogonal:'export'
                        }
                    },
                    {
                        extend: 'csv',
                        className: 'btn btn-primary me-2 rounded',
                        exportOptions: {
                            columns: ':not(.noexport)',
                            orthogonal:'export'
                        }
                    },
                ],
                columnDefs: [
                    { responsivePriority: 1, targets: 0 }, // First visible column has top priority (e.g. proposal_number
                    { responsivePriority: 2, targets: -1 }, // If the actions is the last entry in columns then this will make it 2nd top priority soo as long as the screen is a decent size it will always be shown
                ],
                columns: [
                    {
                        data: "requirement",
                        //title: originatingLicence,
                        //orderable: false,
                        'render': function (value, type) {
                            var result= helpers.dtPopover(value);
                            //return result;
                            return type=='export' ? value : result;
                        },
                        // 'createdCell': helpers.dtPopoverCellFn,
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
                                /*
                                if(full.copied_from==null)
                                {
                                    links +=  `<a href='#' class="editRequirement" data-id="${full.id}">Edit</a><br/>`;
                                }
                                */
                                links +=  `<a href='#' class="editRequirement" data-id="${full.id}">Edit</a><br/>`;
                                links +=  `<a href='#' class="deleteRequirement" data-id="${full.id}">Delete</a><br/>`;
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
                            return links;
                        },
                        orderable: false,
                        defaultContent: '',
                    }
                ],
                processing: true,
                drawCallback: function () {
                    if (
                        vm.$refs.target_requirements_datatable &&
                        vm.$refs.target_requirements_datatable.table
                    ) {                    
                        $(vm.$refs.target_requirements_datatable.table).find('tr:last .dtMoveDown').remove();
                        $(vm.$refs.target_requirements_datatable.table).children('tbody').find('tr:first .dtMoveUp').remove();
                    }
                    // Remove previous binding before adding it
                    $('.dtMoveUp').unbind('click');
                    $('.dtMoveDown').unbind('click');

                    // Bind clicks to functions
                    $('.dtMoveUp').click(vm.moveUp);
                    $('.dtMoveDown').click(vm.moveDown);
                    //$(this).show();
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
        RequirementDetail,
        FormSection
    },
    computed:{
        hasAssessorMode(){
            return this.proposal.assessor_mode.has_assessor_mode;
        },
        sectionTitle(){
            let titleText = 'Requirements for ';
            if (this.targetApprovalLodgementNumber) {
                titleText += this.targetApprovalLodgementNumber;
            } else {
                titleText += 'New Licence';
            }
            return titleText;
        },

        /*
        targetApprovalLodgementNumber: function() {
            let returnVal = '';
            if (this.targetApproval) {
                returnVal = this.targetApproval.lodgement_number;
            }
            return returnVal;
        },
        originatingLicence() {
            if (this.proposal) {
                return this.proposal.lodgement_number;
            }
        },
        */
    },
    methods:{
        addRequirement(){
            // this.keyVersion += 1;
            this.$nextTick(() => {
                this.$refs.target_requirement_detail.isModalOpen = true;
            });
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
                        vm.$refs.target_requirements_datatable.vmDataTable.ajax.reload(
                            helpers.enablePopovers,
                            false
                        );
                    }).catch((error) => {
                        console.log(error);
                    });
                }
            },(error) => {
                // User cancelled the action
                console.log(error);
            });
        },
        fetchRequirements(){
            let vm = this;
            let url = api_endpoints.proposal_standard_requirements;
            if (this.proposal.proposal_apiary) {
                url = api_endpoints.apiary_standard_requirements;
            }
            fetch(url).then(
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
                this.$refs.target_requirement_detail.requirement = data;
                this.$refs.target_requirement_detail.requirement.due_date =  data.due_date != null && data.due_date != undefined ? moment(data.due_date).format('DD/MM/YYYY'): '';
                data.standard ? $(this.$refs.target_requirement_detail.$refs.standard_req).val(data.standard_requirement).trigger('change'): '';
                this.addRequirement();
            }).catch((error) => {
                console.log(error);
            })
        },
        updatedRequirements(){
            this.$refs.target_requirements_datatable.vmDataTable.ajax.reload();
        },
        eventListeners(){
            let vm = this;
            vm.$refs.target_requirements_datatable.vmDataTable.on('click', '.deleteRequirement', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.removeRequirement(id);
            });
            vm.$refs.target_requirements_datatable.vmDataTable.on('click', '.editRequirement', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.editRequirement(id);
            });
        },
        sendDirection(req,direction){
            let movement = direction == 'down'? 'move_down': 'move_up';
            fetch(helpers.add_endpoint_json(api_endpoints.proposal_requirements,req+'/'+movement)).then(async (response) => {
                if (!response.ok) { return response.json().then(err => { throw err }); }
            }).catch((error) => {
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
            var table = this.$refs.target_requirements_datatable.vmDataTable;
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
    created: function() {
        /*
        // load targetApproval
        this.$http.get(helpers.add_endpoint_json(api_endpoints.approvals,this.proposal.approval.id))
        .then((response) => {
            //vm.$refs.requirements_datatable.vmDataTable.ajax.reload();
            //Object.assign(this.targetApproval, response.body);
            this.targetApproval = helpers.copyObject(response.body);
        }, (error) => {
            console.log(error);
        });
        */
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
