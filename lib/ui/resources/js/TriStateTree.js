/**
 * @class Ext.ux.grid.TriStateTree
 * @extends   Ext.tree.Panel
 * @requires Ext.selection.TreeModel
 * @version 0.1
 * @author Lev Savranskiy
 * @link http://wap7.ru/folio/ext-tri-state-tree
 * @contact  levsavranskiy at gmail.com


 <h3>Features:</h3>

 <ol>
 <li> Extends Ext.tree.Panel
 </li>
 <li> If a parent node is checked / unchecked, all its child nodes are automatically checked / unchecked too.
 </li>


 <li> If only some children of a node are selected, its checkbox remains checked, but with a third visual state,
 using a darkened background.
 <p class="small">
 * A single file (checkboxes.gif) defines all the three images.
 </p>
 </li>

 <li> getSelections method returns list of checked data as objects for simple backend serialization as [{id: 123}, {id: 345} ...]
 <p class="small">

 * If called with parameter id_only (bool) - it returns list of checked data as [123, 345]<br/>
 * If ALL_ID value found, only ALL_ID returned. as [{id: 1}]
 * By default only leaf nodes id`s returned. You can configure it via 'returnLeafsOnly' property.
 </p>
 </li>
 <li> setSelections method consumes  list of IDS   [123,456,789] or objects [{id: 123}, {id: 345}]<br/>

 <p class="small">
 * Pass ALL_ID value in input list to check all.
 </p>
 </li>
 </ol>


 <h3>How to use:</h3>

 <ol>
 <li>Download and unzip <a href="ext-tri-state-tree.zip">archive</a></li>
 <li>Set 'returnLeafsOnly' to FALSE if you want to get all selected nodes</li>
 <li>Set ALL_ID value to match your backend logic for SELECT ALL (1 by default)</li>
 <li>Fill Ext.data.TreeStore with own data in initComponent() or via setRootNode()</li>
 <li>Place checkboxes.gif in 'img' folder</li>
 <li>Apply next rules to your stylesheet</li>

 <pre>
 div.x-panel-body input.x-tree-checkbox {
        background-image:url(../img/checkbox.gif) !important;
        }

 div.x-panel-body .x-tree-checkbox-checked-disabled input.x-tree-checkbox {
        background-position: 0 -26px;
        }
 </pre>

 </ol>

 */

Ext.define('Ext.ux.grid.TriStateTree', {
    extend: 'Ext.tree.Panel',
    rootVisible: true,
    useArrows: true,
    frame: false,
    header: false,
    style: 'margin: 0px 0px',
    disabledCls: 'x-tree-checkbox-checked-disabled',
    ALL_ID: 1,
    returnLeafsOnly: true,
    width: 350,
    height: 200,
    selModel: new Ext.selection.TreeModel({
        mode: 'MULTI',
        ignoreRightMouseSelection: true
    }),

    listeners: {
        checkchange: function (node, check) {
            var me = this;

            node.set('cls', '');
            me.updateParentCheckedStatus(node);

            if (node.hasChildNodes()) {
                node.eachChild(this.setChildrenCheckedStatus);
            }

            if (node.get('id') == this.ALL_ID) {
                //debug('[root checked]');

                //unsetThirdState for all
                me.getRootNode().cascadeBy(function () {

                    me.unsetThirdState(this);
                });
            }


        },
        beforeitemclick: function(dv, record, item, index, e) {
            // if (isTreeFiltered) {
            //     console.log('before click');
            //     e.preventDefault();
            //     return false;
            // }
        },
        beforeitemdblclick: function(dv, record, item, index, e) {
            // if (isTreeFiltered) {
            //     console.log('before click');
            //     e.preventDefault();
            //     return false;
            // }
        }
    },

    // Propagate change downwards (for all children of current node).
    setChildrenCheckedStatus: function (current) {

        // if not root checked
        if (current.parentNode) {
            var parent = current.parentNode;
            current.set('checked', parent.get('checked'));
        }


        if (current.hasChildNodes()) {
            current.eachChild(arguments.callee);
        }
    },

    // Propagate change upwards (if all siblings are the same, update parent).
    updateParentCheckedStatus: function (current) {
        var me = this,
            currentChecked = current.get('checked'),
            currentId = current.get('id');


        if (current.parentNode) {

            var parent = current.parentNode;
            var checkedCount = 0;
            var checkedCountChildren = 0;
            parent.eachChild(function (n) {
                // debug( n.get('text'))
                checkedCount += (n.get('checked') ? 1 : 0);
            });

            current.eachChild(function (n) {
                // debug( n.get('text'))
                checkedCountChildren += (n.get('checked') ? 1 : 0);
            });

            // Children have same value if all of them are checked or none is checked.
            var allMySiblingsHaveSameValue = (checkedCount == parent.childNodes.length) || (checkedCount == 0);
            var allMyChildrenHaveSameValue = (checkedCountChildren == current.childNodes.length) || (checkedCountChildren == 0);


//            debug('[current] ' + current.get('text'));
//            debug('[currentChecked] ' + currentChecked);
//            debug('[parent ] ' + parent.get('text'));
//            debug('[allMySiblingsHaveSameValue] ' + allMySiblingsHaveSameValue);
//            debug('[allMyChildrenHaveSameValue] ' + allMyChildrenHaveSameValue);
//            debug('--------------');

            var setParentVoid = true;


            // check if current node has any visible state.
            if (me.isThirdState(current) || currentChecked) {
                setParentVoid = false;
            }

            // if not - clear parent`s class
            if (setParentVoid) {
                me.unsetThirdState(parent);
            }

            if (allMySiblingsHaveSameValue) {

                // All  the Siblings  are same, so apply value to the parent.
                var checkedValue = (checkedCount == parent.childNodes.length);
                parent.set('checked', checkedValue);

                me.unsetThirdState(parent);
                // modify  Root based on it`s Children Have Same Value

                if (parent == me.getRootNode()) {
                    if (allMyChildrenHaveSameValue) {
                        me.unsetThirdState(me.getRootNode());
                    } else {
                        me.setThirdState(me.getRootNode());
                    }
                }


            } else {

                // Not all  the children are same, so set root node to third state.

                me.setThirdState(me.getRootNode());

                if (checkedCount) {
                    // At least one sibling is checked, so set parent node to third state.
                    me.setThirdState(parent);

                } else {

                    parent.set('checked', false);
                }


            }

            me.updateParentCheckedStatus(parent);
        }
    },

    isThirdState: function (node) {
        return  node.get('cls') == this.disabledCls;

    },

    setThirdState: function (node) {
        node.set('cls', this.disabledCls);
        node.set('checked', false);
    },

    unsetThirdState: function (node) {
        node.set('cls', '');
    },

    getSelections: function (id_only) {
        var me = this;

        //debug('[accessPanel getSelections]');

        try {
            var grid_selections = me.getView().getChecked(),
                allFound = false,
                result = [];


            Ext.Array.each(grid_selections, function (rec) {

                var pushdata = false;

                //  find all checked items
                if (rec.get('id') ) {

                    if (me.returnLeafsOnly ){
                        if (rec.get('leaf') === true){
                            pushdata = true;
                        }
                    }   else{
                        pushdata = true;
                    }
                    if (pushdata){
                        result.push(id_only == true ?  rec.get('id') : {id: rec.get('id')});
                    }

                }

                //  if NODE 'ALL' checked  - no children required
                if (rec.get('id') == me.ALL_ID) {
                    allFound = true;
                }
            });


            if (allFound) {
                result = id_only ? [  me.ALL_ID ] : [ {id: me.ALL_ID} ];
            }

            //debug(result);
            return result;
        } catch (e) {

            debug('[error in accessPanel getSelections]');
            debug(e);
        }
    },

    setSelections: function (ids) {

        var me = this;
        //  me.stopListener = true;

        //debug('[accessPanel setSelections]');
        // debug(ids);


        if (ids[0] && ids[0]['id']){

            ids = Ext.Array.pluck(ids, 'id');
        }

        // check RootNode or do cascade checking

        if (ids.indexOf(me.ALL_ID) > -1) {
            me.getRootNode().set('checked', true);
            me.getRootNode().eachChild(me.setChildrenCheckedStatus);
        } else {


            me.getRootNode().cascadeBy(function () {

                var currNode = this;

                if (currNode.get('leaf')) {
                    currNode.set('checked', ids.indexOf(currNode.get('id')) > -1);
                    me.updateParentCheckedStatus(currNode);
                }
            });
        }


    }

    // initComponent: function () {
    //     var me = this;

    //     //debug('[ACCESS PANEL]');

    //     var data = {
    //         text: 'SELECT ALL (id'+me.ALL_ID + ')',
    //         id: me.ALL_ID,
    //         expanded: true,
    //         checked: false,
    //         children: [
    //             { text: "id2 homework ",  checked: false,    expanded: true,
    //                 id  : 2,
    //                 children: [
    //                 {       id  : 3,  checked: false, text: "id3 book report ",  leaf: true },
    //                 {       id  : 4,   checked: false, text: "id4 algebra ", leaf: true}

    //             ] },
    //             {        id  : 5,  checked: false, text: "id5 food ", expanded: true, children: [
    //                 {        id  : 6,  checked: false,   text: "id6 meat ", leaf: true },
    //                 {        id  : 7,  checked: false,  text: "id7 milk ", leaf: true}
    //             ] },
    //             {        id  : 8,  checked: false,  text: "id8 plans ", expanded: true, children: [
    //                 {        id  : 9, checked: false,   text: "id9 vacation ", leaf: true },
    //                 {        id  : 10,  checked: false,  text: "id10 rule the world ", leaf: true}
    //             ] }
    //         ]
    //     };


    //     this.store = Ext.create('Ext.data.TreeStore', {
    //         fields: ['text' , 'id'],
    //         root: data

    //     });

    //     this.callParent(arguments);

    // }

});