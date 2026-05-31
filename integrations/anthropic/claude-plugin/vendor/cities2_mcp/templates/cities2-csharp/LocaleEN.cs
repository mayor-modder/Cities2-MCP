using Colossal;
using System.Collections.Generic;

namespace {{ROOT_NAMESPACE}};

public class LocaleEN : IDictionarySource
{
    private readonly Setting _setting;

    public LocaleEN(Setting setting)
    {
        _setting = setting;
    }

    public IEnumerable<KeyValuePair<string, string>> ReadEntries(IList<IDictionaryEntryError> errors, Dictionary<string, int> indexCounts)
    {
        return new Dictionary<string, string>
        {
            { _setting.GetSettingsLocaleID(), "{{DISPLAY_NAME_CS_STRING}}" },
            { _setting.GetOptionTabLocaleID(Setting.kSection), "Main" },
            { _setting.GetOptionLabelLocaleID(nameof(Setting.EnableFeature)), "Enable feature" },
            { _setting.GetOptionDescLocaleID(nameof(Setting.EnableFeature)), "Enable core functionality for this mod." },
        };
    }

    public void Unload()
    {
    }
}
