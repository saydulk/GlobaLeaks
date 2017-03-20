angular.module('GLClient')
.controller('MultiTenantCtrl', ['$scope', function($scope) {

  $scope.new_tenant = {};

  $scope.add_tenant = function() {
    var new_tenant = new $scope.admin_utils.new_tenant();
    new_tenant.hostname = $scope.new_tenant.hostname;

    new_tenant.$save(function(new_tenant){
      $scope.admin.tenants.push(new_tenant);
      $scope.new_tenant = {};
    });
  }
}])
.controller('TenantEditorCtrl', ['$scope', 'AdminTenantResource', function($scope, AdminTenantResource) {
  $scope.delete_tenant = function(tenant) {
    AdminTenantResource.delete({
      id: tenant.id
    }, function(){
      var idx = $scope.admin.tenants.indexOf(tenant);
      $scope.admin.tenants.splice(idx, 1);
    });
  };
}]);
