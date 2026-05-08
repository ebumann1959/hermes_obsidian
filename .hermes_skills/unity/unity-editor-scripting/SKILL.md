---
name: unity-editor-scripting
description: "Unity C# editor scripting via SSH — write, debug, and run MenuItem/EditorWindow scripts remotely. Covers headless batchmode, common compile errors in Unity 6000.4, X509Certificate2/Mono TLS issues, and NavMesh setup."
category: unity
---

# Unity Editor Scripting via SSH

Remote development of Unity C# editor scripts via SSH to MX25Rig PC. Covers MenuItem/EditorWindow authoring, headless batchmode execution, common compile errors, TLS certificate handling, and NavMesh setup.

PC (MX25Rig): `10.0.0.91`, MX Linux
Project: `/mnt/Data/show_runner/`
Unity: `/home/Evan/Unity/Hub/Editor/6000.4.2f1/Editor/Unity`

---

## Workflow: Push + Verify

1. Write/patch `.cs` file locally
2. `scp file.cs user@host:"/path/to/project/Assets/.../file.cs"`
3. Wait for Unity compile (bottom-right status bar: "Compiling...")
4. Check errors: `ssh user@host 'grep error ~/.config/unity3d/Editor.log | tail -5'`
5. If clean, invoke via MenuItem or re-run

---

## MenuItem and EditorWindow Basics

Scripts live in `Assets/show_runner/SceneSetup/` or any `Assets/*/` folder. Unity auto-compiles on save.

```csharp
#if UNITY_EDITOR
using UnityEngine;
using UnityEditor;

public class MyTool
{
    [MenuItem("ShowRunner/My Tool")]
    public static void DoThing()
    {
        Debug.Log("Works!");
    }
}
#endif
```

Menu appears at `ShowRunner/` in Unity's top menu bar. Sub-menus: `"ShowRunner/SubMenu/My Tool"`.

---

## Headless Batchmode via SSH

Use `xvfb-run -a` to run Unity editor scripts without a display:

```bash
ssh user@host "cd '/path/to/project' && xvfb-run -a /path/to/Unity -batchmode -projectPath '/path/to/project' -executeMethod MyMenuItem.DoThing -quit -logFile /tmp/unity_batch.log"
```

**Common issues:**
- **GLX errors**: `xvfb-run -a` handles this (creates virtual X server)
- **Exit 0 but no compile**: Missing `xvfb-run` — Unity can't open display and exits silently
- **GTK dialog hangs**: Unity's quit confirmation dialog hangs batchmode. Pipe `echo y`:
  ```bash
  ssh user@host 'echo "y" | xvfb-run -a /path/to/Unity -batchmode -projectPath "/path/to/project" -executeMethod MyMenuItem.DoThing -quit'
  ```

Always verify compile success:
```bash
ssh user@host 'grep -E "error CS|Scripts have compiler errors" ~/.config/unity3d/Editor.log'
# Must return empty (0 matches) for success
```

**Editor.log location:** `~/.config/unity3d/Editor.log` — NOT `~/Logs/Editor.log` (stale symlink on some setups).

---

## Common Compile Errors in Unity 6000.4

### FindObjectsOfType API Changes

```csharp
// ✅ Works despite deprecation warning:
CharacterController[] ccs = Object.FindObjectsOfType<CharacterController>();

// ❌ CS1503 — enum overload doesn't exist in this form:
CharacterController[] ccs = Object.FindObjectsOfType<CharacterController>(FindObjectsInactive.Exclude);

// ❌ CS1503 — generic overload with sort mode also broken:
CharacterController[] ccs = Object.FindObjectsOfType<CharacterController>(FindObjectsSortMode.None);
```

Use the no-arg form and filter scene objects manually if needed.

### Scene Objects Only (Exclude Prefab Assets)

```csharp
GameObject[] allGobs = (GameObject[])Resources.FindObjectsOfTypeAll(typeof(GameObject));
var sceneGobs = new System.Collections.Generic.List<GameObject>();
Scene activeScene = EditorSceneManager.GetActiveScene();
foreach (var gob in allGobs)
    if (gob != null && gob.gameObject.scene == activeScene)
        sceneGobs.Add(gob);
```

### GameObject Type Confusion

`GameObject` has no `.localRotation`, `.localPosition`, `.SetParent`. Use `child.transform.localPosition`, etc.

### NavMeshBuilder Deprecation

Unity 6000.4 deprecated `UnityEditor.NavMeshBuilder`. Use instance-based `NavMeshSurface`:
```csharp
var surface = ground.GetComponent<NavMeshSurface>();
if (surface == null) surface = ground.AddComponent<NavMeshSurface>();
surface.BuildNavMesh();
```
Requires `com.unity.ai.navigation` in Packages (`"com.unity.ai.navigation": "2.0.7"` in manifest.json).

### Missing Usings

| Missing | Required |
|---------|----------|
| Scene management | `using UnityEditor.SceneManagement;` |
| NavMesh surfaces | `using Unity.AI.Navigation;` |
| GameObject/Transform | `using UnityEngine;` |

### CS1631: Cannot Yield in Catch Clause

`yield return` cannot appear inside a `catch` block in C# iterator methods:
```csharp
// ❌ Illegal:
catch (SocketException ex) { yield return null; }

// ✅ Legal — use boolean flag:
bool acceptError = false;
try { newClient = _listener.EndAccept(_acceptAr); }
catch (SocketException ex) { acceptError = true; }
if (acceptError) { _acceptAr = _listener.BeginAccept(null, null); yield return null; }
```

### CS0101: Duplicate Type Name

Unity merges ALL .cs compilation units at compile time. If two files both define `public class Foo`, you get CS0101. This commonly happens when:
- A nested class inside one file has the same name as a standalone file
- A component is defined both in the main script and in a separate component file

**Example of the mistake:**
```csharp
// CharacterRegistry.cs — WRONG (nested class duplicates BillboardLabel.cs):
public class CharacterRegistry : MonoBehaviour
{
    // ... hundreds of lines ...
    public class BillboardLabel : MonoBehaviour  // CS0101 — already defined in BillboardLabel.cs!
    {
        public string text;
    }
}
```

**Fix:** Never define nested MonoBehaviour classes. Use standalone component files for each behaviour. If a class name is already used in `Assets/ShowRunner/Scripts/`, reference it via `AddComponent<BillboardLabel>()` instead of defining it inline.

### StopCoroutine + StartCoroutine Mismatch

`StopCoroutine(string)` only stops coroutines started via `StartCoroutine(string)`. Using it with `StartCoroutine(IEnumerator)` is a no-op — the coroutine keeps running.

```csharp
// ❌ WRONG — these are incompatible:
StopCoroutine("Move_" + character_id);           // string overload
StartCoroutine(MoveOverTime(character_id, ...)); // IEnumerator overload — NOT stopped!

// ✅ CORRECT — track with Dictionary<string, Coroutine>:
private readonly Dictionary<string, Coroutine> _activeMoves = new Dictionary<string, Coroutine>();

void MoveCharacter(string character_id, Vector3 target)
{
    if (_activeMoves.TryGetValue(character_id, out var prev) && prev != null)
        StopCoroutine(prev);
    _activeMoves[character_id] = StartCoroutine(MoveOverTime(character_id, target, 0.5f));
}

void DespawnCharacter(string character_id)
{
    _activeMoves.Remove(character_id);
}
```

When writing coroutine-based animation/movement, always use the Dictionary approach to allow interruption of in-progress tweens.

---

## Opening a Scene in Editor Scripts

```csharp
using UnityEditor.SceneManagement;
const string TARGET_SCENE = "Assets/Scenes/ShowRunnerScene.unity";
Scene scene = SceneManager.GetActiveScene();
if (string.IsNullOrEmpty(scene.path) || scene.path != TARGET_SCENE)
{
    EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo();
    scene = EditorSceneManager.OpenScene(TARGET_SCENE, OpenSceneMode.Single);
}
```

---

## X509Certificate2 + SslStream on Unity/Mono/Linux

Mono's certificate loader does NOT support modern PFX formats (PBES2/AES-256-CBC). `X509Certificate2` fails silently or throws on load.

**Solution — use `EphemeralKeySet`:**
```csharp
// ❌ Fails on Mono/Linux:
_cert = new X509Certificate2("/path/to/cert.pfx", "password");

// ✅ Works:
_cert = new X509Certificate2("/path/to/cert.pfx", "password", X509KeyStorageFlags.EphemeralKeySet);
```

`EphemeralKeySet` keeps the key purely in-memory, bypassing Mono's broken disk-based import.

**Generating compatible PFX:**
```bash
openssl req -x509 -newkey rsa:2048 -keyout comms_key.pem -out comms_cert.pem -days 365 -nodes -subj '/CN=showrunner'
openssl pkcs12 -export -in comms_cert.pem -inkey comms_key.pem -out comms.pfx -passout pass:showrunner
# Verify:
openssl pkcs12 -info -in comms.pfx -passin pass:showrunner -noout
```

**Other Mono/Certificate pitfalls:**
- Empty password `""` often fails — use non-empty
- `MachineKeySet` fails without root — use `EphemeralKeySet` or `UserKeySet`
- Unity Editor must be in **Play mode** for `Start()` / `StartServer()` to run (game loop must be executing)

---

## UnityComms HTTP Server — Play Mode Only

The HTTP server (`StartServer()` coroutine) only starts when the Unity game loop is running. In Edit mode (editor open but Play not pressed), the server is NOT listening.

**Detecting a crashed Editor:** When Unity crashes via `-executeMethod`, it spawns `UnityBugReporter`:
```bash
ps aux | grep UnityBugReporter | grep --origin EditorCrash
```

---

## NavMesh Setup

1. Ensure `com.unity.ai.navigation` is in Packages
2. Create a `NavMeshBaker.cs` MenuItem:
```csharp
#if UNITY_EDITOR
using UnityEngine;
using UnityEditor;
using Unity.AI.Navigation;

public class NavMeshBaker
{
    [MenuItem("ShowRunner/Bake NavMesh")]
    public static void Bake()
    {
        GameObject ground = null;
        foreach (var root in EditorSceneManager.GetActiveScene().GetRootGameObjects())
        {
            if (root.name.ToLower().Contains("ground")) { ground = root; break; }
            foreach (Transform child in root.transform)
                if (child.name.ToLower().Contains("ground"))
                    { ground = child.gameObject; break; }
        }
        if (ground == null) { Debug.LogError("[NavMeshBaker] No Ground found."); return; }
        var surface = ground.GetComponent<NavMeshSurface>();
        if (surface == null) surface = ground.AddComponent<NavMeshSurface>();
        surface.BuildNavMesh();
        Debug.Log("[NavMeshBaker] Done.");
    }
}
#endif
```
3. Run **ShowRunner → Bake NavMesh** after scene setup
4. Bake requires a Ground object with a collider in the scene

---

## Edit Mode vs Play Mode — Critical Distinction

| Mode | Editor window | Game loop | Start() fires | HTTP server |
|------|--------------|-----------|---------------|-------------|
| Edit | Open | Not running | NO | NO |
| Play | Open + playing | Running | YES | YES |

`EditorApplication.isPlaying = true` via `-executeMethod` CANNOT substitute for pressing Play — it requires an active display.

---

## Unity Lockfile After Headless Compile

After a headless `-batchmode -quit`, Unity leaves a `UnityLockfile` in `Temp/`. If the GUI editor was also running, this lockfile prevents reopening.

**Fix:**
```bash
ssh 10.0.0.91 "rm -vrf '/mnt/Data/show_runner/Temp/'; rm -v '/mnt/Data/show_runner/Temp/UnityLockfile' 2>/dev/null || true"
```

---

## References

- `references/unity-comms-tls-cert-fix.md` — X509Certificate2 Mono workaround (demoted from unity-comms-tls-cert-fix skill)
