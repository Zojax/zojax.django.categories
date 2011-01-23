$(function() {
  $(".categories-tree").treeview({collapsed: true});
  $(".categories-tree input[type='checkbox'][checked='checked']").each(function(index, el) {
     $(el).parents('li.expandable').find('.expandable-hitarea').removeClass('expandable-hitarea').addClass('collapsable-hitarea');
	 $(el).parents('li.expandable').removeClass('expandable').addClass('collapsable');
     $(el).parents('li.lastExpandable').find('.lastExpandable-hitarea').removeClass('lastExpandable-hitarea').addClass('lastCollapsable-hitarea');
	 $(el).parents('li.lastExpandable').removeClass('lastExpandable').addClass('lastCollapsable');
	 $(el).parents('ul').show();
  });
});
