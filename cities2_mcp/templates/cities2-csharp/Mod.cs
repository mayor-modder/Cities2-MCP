using Colossal.IO.AssetDatabase;
using Colossal.Logging;
using Game;
using Game.Modding;
using Game.SceneFlow;
using Unity.Entities;
{{USING_HARMONY}}

namespace {{ROOT_NAMESPACE}};

public class Mod : IMod
{
    public static ILog Log = LogManager.GetLogger(nameof({{ROOT_NAMESPACE}})).SetShowsErrorsInUI(false);
{{HARMONY_FIELD}}
{{SETTING_FIELD}}

    public void OnLoad(UpdateSystem updateSystem)
    {
        Log.Info(nameof(OnLoad));

        if (GameManager.instance.modManager.TryGetExecutableAsset(this, out var asset))
        {
            Log.Info($"Current mod asset at {asset.path}");
        }

{{ONLOAD_SETTINGS}}{{ONLOAD_LOCALIZATION}}{{ONLOAD_HARMONY}}    }

    public void OnDispose()
    {
        Log.Info(nameof(OnDispose));
{{ONDISPOSE_SETTINGS}}{{ONDISPOSE_HARMONY}}    }
}
