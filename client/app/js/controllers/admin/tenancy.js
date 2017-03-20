angular.module('GLClient')
.controller('MultiTenantCtrl', ['$scope', function($scope) {
   $scope.newTenant = {
     hostname: '', 
   };

   $scope.addTenant = function() {
     tenant = {
        hostname: $scope.newTenant.hostname,
        tid: Math.random().toString(36).substring(7), // TODO take me out to the ball-park
     };
     $scope.admin.tenants.push(tenant);
   
     $scope.newTenant = {};
   }
}])
.controller('TenantEditorCtrl', ['$scope', function($scope) {
  $scope.deleteTenant = function(tenant, $index) {
    console.log('Removing', tenant);
    $scope.admin.tenants.remove($index); 
  } 

  $scope.saveTenant = function() {}  // TODO

  $scope.editing = false;
  $scope.toggleEditing = function () {
    $scope.editing = !$scope.editing;
  };
}]);
