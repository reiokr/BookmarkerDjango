from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.

    Audit spec §7 end-state: this class is attached to exactly ONE view
    (``BmDetailView``), whose ``get_object`` calls ``check_object_permissions``
    on every request -- so it executes and is load-bearing there. Safe
    methods pass through here; BmDetailView additionally owner-scopes reads
    in get_object, because foreign bookmarks must be invisible even to GET.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the obj.
        return obj.owner == request.user



