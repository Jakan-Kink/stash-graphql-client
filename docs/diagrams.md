# Architecture Diagrams

This page contains the architecture diagrams for stash-graphql-client.

## Three-Layer Architecture

```mermaid
graph TB
    User[Developer Code] --> Client[Layer 1: StashClient]
    User --> Types[Layer 2: Pydantic Types]
    User --> Store[Layer 3: StashEntityStore]

    Client -->|executes| GraphQL[GraphQL API]
    Client -->|returns| Types

    Types -->|validates| Pydantic[Pydantic v2]
    Types -->|wrap validator| IdentityMap[Identity Map]

    Store -->|uses| Client
    Store -->|manages| IdentityMap
    Store -->|caches| Types

    GraphQL -->|responses| Client

    style Client fill:#2E86AB,color:#fff
    style Types fill:#F77F00,color:#fff
    style Store fill:#8338EC,color:#fff
    style IdentityMap fill:#06A77D,color:#fff
```

## Identity Map Flow (Wrap Validator)

```mermaid
sequenceDiagram
    participant Code as Developer Code
    participant Constructor as Scene.from_dict()
    participant Validator as @model_validator(mode='wrap')
    participant Cache as Identity Map Cache
    participant Pydantic as Pydantic Handler
    participant Object as Scene Instance

    Code->>Constructor: Scene.from_dict({"id": "123", ...})
    Constructor->>Validator: Intercept construction

    alt Cache Hit
        Validator->>Cache: Check cache[(type, id)]
        Cache-->>Validator: Found cached instance
        Validator->>Object: Merge new fields
        Validator-->>Code: Return cached instance
    else Cache Miss
        Validator->>Cache: Not found
        Validator->>Validator: Process nested objects
        Validator->>Pydantic: handler(processed_data)
        Pydantic->>Object: Construct & validate
        Object-->>Validator: New instance
        Validator->>Cache: Store instance
        Validator-->>Code: Return new instance
    end

    Note over Validator,Cache: Cache check happens<br/>BEFORE Pydantic validation
```

## UNSET Pattern - Three States

```mermaid
stateDiagram-v2
    [*] --> UNSET: Default state
    UNSET --> Value: Assign value
    UNSET --> Null: Assign None
    Value --> Value: Update value
    Value --> Null: Assign None
    Value --> UNSET: Reset to UNSET
    Null --> Value: Assign value
    Null --> UNSET: Reset to UNSET
    Null --> Null: Stays None

    note right of UNSET
        Field never queried
        or never set.
        Excluded from
        to_graphql()
    end note

    note right of Null
        Explicitly set
        to null.
        Included in
        to_graphql()
    end note

    note right of Value
        Has actual value.
        Included in
        to_graphql()
    end note
```

## Nested Cache Lookup Process

```mermaid
flowchart TD
    Start[from_dict called with data] --> HasStore{Has store?}
    HasStore -->|No| DirectPydantic[Pass to Pydantic]
    HasStore -->|Yes| CheckID{Has 'id' field?}

    CheckID -->|No| DirectPydantic
    CheckID -->|Yes| CacheKey[Build cache key: type, id]

    CacheKey --> CacheCheck{In cache?}
    CacheCheck -->|Yes + Not Expired| ReturnCached[Return cached instance]
    CacheCheck -->|Yes + Expired| Evict[Evict from cache]
    CacheCheck -->|No| ProcessNested

    Evict --> ProcessNested[Process nested objects]
    ProcessNested --> IterateFields[Iterate model fields]

    IterateFields --> CheckField{Field is<br/>nested object?}
    CheckField -->|No| NextField[Next field]
    CheckField -->|Yes| NestedCache{Nested obj<br/>in cache?}

    NestedCache -->|Yes| ReplaceWithCached[Replace dict with<br/>cached instance]
    NestedCache -->|No| KeepDict[Keep as dict]

    ReplaceWithCached --> NextField
    KeepDict --> NextField
    NextField --> MoreFields{More fields?}

    MoreFields -->|Yes| CheckField
    MoreFields -->|No| CallHandler[Call Pydantic handler]

    CallHandler --> Validate[Pydantic validates]
    Validate --> NewInstance[New instance created]
    NewInstance --> CacheNew[Cache new instance]
    CacheNew --> ReturnNew[Return new instance]

    ReturnCached --> End[Instance]
    ReturnNew --> End
    DirectPydantic --> End

    style CacheCheck fill:#06A77D,color:#fff
    style ReturnCached fill:#06A77D,color:#fff
    style ProcessNested fill:#F77F00,color:#fff
    style Validate fill:#2E86AB,color:#fff
```

## Relationship Sync Flow

```mermaid
sequenceDiagram
    participant Code as Developer Code
    participant Scene as Scene Instance
    participant Studio as Studio Instance
    participant Metadata as RelationshipMetadata
    participant Sync as _sync_inverse_relationship()

    Code->>Scene: scene.studio = studio_obj
    Scene->>Scene: __setattr__("studio", studio_obj)
    Scene->>Metadata: Get relationship metadata
    Metadata-->>Scene: {inverse_query_field: "scenes", ...}

    Scene->>Sync: _sync_inverse_relationship("studio", studio_obj)

    alt Inverse field loaded
        Sync->>Studio: Check if studio.scenes is loaded
        Studio-->>Sync: is_set(studio.scenes) = True
        Sync->>Studio: studio.scenes.append(scene)
        Note over Scene,Studio: Bidirectional sync complete
    else Inverse field not loaded
        Sync->>Studio: studio.scenes is UNSET
        Note over Scene,Studio: Skip sync (would need to query)
    end

    Sync-->>Code: Relationship set
```

## Field-Aware Population

```mermaid
flowchart TD
    Start[store.populate called] --> CheckReceived{Check<br/>_received_fields}

    CheckReceived --> CalcMissing[Calculate missing:<br/>requested - received]
    CalcMissing --> HasMissing{Has missing<br/>fields?}

    HasMissing -->|No| Return[Return instance]
    HasMissing -->|Yes| BuildQuery[Build GraphQL query<br/>for missing fields only]

    BuildQuery --> Execute[Execute query]
    Execute --> Response[GraphQL response]

    Response --> MergeFields[Merge new fields into<br/>cached instance]
    MergeFields --> UpdateReceived[Update _received_fields]
    UpdateReceived --> Return

    style CheckReceived fill:#F77F00,color:#fff
    style MergeFields fill:#06A77D,color:#fff
    style UpdateReceived fill:#2E86AB,color:#fff
```

## Django-Style Filter Translation

```mermaid
flowchart LR
    Input["rating100__gte=80"] --> Parse[Parse kwargs]
    Parse --> Split[Split on '__']
    Split --> Field[Field: 'rating100']
    Split --> Modifier[Modifier: 'gte']

    Field --> BuildFilter[Build filter object]
    Modifier --> MapModifier[Map to GraphQL modifier]

    MapModifier --> GraphQLMod["GREATER_THAN"]

    BuildFilter --> Combine[Combine field + modifier]
    GraphQLMod --> Combine

    Combine --> Output["{\n  rating100: {\n    value: 80,\n    modifier: 'GREATER_THAN'\n  }\n}"]

    style Input fill:#2E86AB,color:#fff
    style Output fill:#06A77D,color:#fff
```
