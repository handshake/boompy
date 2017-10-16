# Boompy

## How to use it:
```
import boompy
boompy.set_auth({{account_id}}, {{account_username}}, {{account_password}})
acct = boompy.Account(name="test")
acct.save()
```

=======

## Supported Entities
- Account
- Account Group
- Account Group Account
- Account User Role
- Atom
- Environment
- Environment Atom Attachment
- Environment Extensions
- Event
- Installer Token
- Integration Pack
- Integration Pack Instance
- Integration Pack Environment Attachment
- Role

## Supported API Actions
- getAssignableRoles
- provisionPartnerCustomerAccount
- updatePartnerCustomerAccount
