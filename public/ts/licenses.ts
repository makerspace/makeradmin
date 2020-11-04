import * as common from "./common"
import * as login from "./login"
import { logout, UNAUTHORIZED } from "./common";
declare var UIkit: any;


common.documentLoaded().then(() => {
    common.addSidebarListeners();

    const apiBasePath = window.apiBasePath;

    const root = <HTMLElement>document.querySelector("#content");

    const future1 = common.ajax("GET", apiBasePath + "/member/current", null);

    future1.then((member_json) => {
        root.innerHTML = `
            <div class="content-centering">
                <h2>Licenser och Rabatter</h2>
                <p>Det här är en lista med licenser och rabatter som medlemmar i Stockholm Makerspace kan använda fritt.<p>
                <p>Ingen licens eller rabattkod får delas med någon som inte är medlem.</p>
                <div>
                    <h3>Lightburn</h3>
                    <p>Mjukvara som används för att kontrollera laserskäraren på Stockholm Makerspace. Datorerna vid laserskäraren har
                    redan det här programmet installerat så du kan fritt använda det där. Men vill du ha Lightburn på din egen dator
                    så kan du köpa det till ett makerspace-rabatterat pris med koden nedan.</p>
                    <pre><code>Rabattkod: St0ckh0lmM@ker-Sp@ce</code></pre>
                </div>

                <div>
                    <h3>VCarve Pro Makerspace Edition</h3>
                    <p>VCarve Pro finns installerat på CAD-datorerna vid laserskäraren. Det är bara CAD-datorerna som kan generera gkods-filer men du kan skapa projekt på din egen dator, förbereda allt och öppna i CAD-datorn för att spara ut toolpaths osv.
                    <ol>
                    <li>Ladda ner en trial av VCarve Pro och installera.</li>
                    <li>Du hittar denna trial-version <a href="https://www.vectric.com/free-trial/vcarve-pro">här</a>.</li>
                    <li>Starta programmet och under fliken Help hittar du "About VCarve Pro Trial".</li>
                    <li>Där sätter du in vårat Makerspace ID som är <pre><code>B7D8D-0BB4E-E7877-8853E-F49AB-A1D0B-DEE9D</code></pre></li>
                    </ol>
            </div>`;
        
            // <h2>Licenses and discounts</h2>
            // <p>This is a list of licenses and discounts that Stockholm Makerspace members can use freely.</p>
            // <p>Note that no license or discount may be shared with non-members.</p>
            // <div>
            //     <h3>Lightburn</h3>
            //     <p>Software used for controlling the laser cutter at Stockholm Makerspace. The desktop computers next to the laser cutter
            //     already have this program installed and you can use it there. However if you want to use Lightburn on your own
            //     personal computer you can purchase a license with a makerspace discount.</p>
            //     <pre><code>Discount code: St0ckh0lmM@ker-Sp@ce</code></pre>
            // </div>
    }).catch(e => {
        // Probably Unauthorized, redirect to login page.
        if (e.status === UNAUTHORIZED) {
            // Render login
            login.render_login(root, null, null);
        } else {
            UIkit.modal.alert("<h2>Failed to load member info</h2>");
        }
    });
});
