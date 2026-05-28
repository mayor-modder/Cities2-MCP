using Colossal;
using Colossal.IO.AssetDatabase;
using Game.Modding;
using Game.Settings;

namespace {{ROOT_NAMESPACE}};

[FileLocation(nameof({{ROOT_NAMESPACE}}))]
public class Setting : ModSetting
{
    public const string kSection = "Main";

    public Setting(IMod mod) : base(mod)
    {
        SetDefaults();
    }

    [SettingsUIHidden]
    public bool HiddenMarker { get; set; }

    [SettingsUISection(kSection)]
    public bool EnableFeature { get; set; }

    public override void SetDefaults()
    {
        HiddenMarker = true;
        EnableFeature = true;
    }
}
