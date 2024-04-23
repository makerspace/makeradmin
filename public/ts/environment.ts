export enum MobileOperatingSystem {
    iOS = "iOS",
    Android = "Android",
    WindowsPhone = "Windows Phone",
    Unknown = "unknown",
}

/** Determine the mobile operating system. */
export function getMobileOperatingSystem(): MobileOperatingSystem {
    var userAgent =
        navigator.userAgent || navigator.vendor || (window as any).opera;

    // Windows Phone must come first because its UA also contains "Android"
    if (/windows phone/i.test(userAgent)) {
        return MobileOperatingSystem.WindowsPhone;
    }

    if (/android/i.test(userAgent)) {
        return MobileOperatingSystem.Android;
    }

    // iOS detection from: http://stackoverflow.com/a/9039885/177710
    if (/iPad|iPhone|iPod/.test(userAgent) && !(window as any).MSStream) {
        return MobileOperatingSystem.iOS;
    }

    return MobileOperatingSystem.Unknown;
}
