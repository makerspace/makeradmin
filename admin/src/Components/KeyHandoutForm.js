import React from 'react';
import DateTimeShow from "./DateTimeShow";
import TextInput from "./TextInput";
import {withRouter} from "react-router";


class KeyHandoutForm extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            saveDisabled: true,
        };
    }
    
    componentDidMount() {
        const {member} = this.props;
        this.unsubscribe = member.subscribe(() => this.setState({saveDisabled: !member.canSave()}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }

    render() {
        const {member, onSave, onDelete} = this.props;
        const {saveDisabled} = this.state;
        
        return (
		<div className="meep">

		<form className="uk-form" onSubmit={(e) => {e.preventDefault(); onSave(); return false;}}>
		
		<div className="uk-section">
    			<div className="uk-container">
				<h2>1. Ta emot signerat labbmedlemsavtal</h2>
				Kontrollera att labbmedlemsavtalet är signerat och säkerställ att rätt medlemsnummer står väl synligt på labbmedlemsavtalet. 	
			</div>
			    <fieldset>
			        <input className="uk-checkbox" type="checkbox"/>
			   	<label> Signerat labbmedlemsavtal mottaget.</label> 
				</fieldset>

		</div>

		<div className="uk-section">
    			<div className="uk-container">
				<h2>2. Kontrollera legitimation</h2>
				Kontrollera personens legitimation och för in personnummret i fältet nedan. Nyckel kan endast lämnas ut till personen som skall bli medlem . 
			</div>

			    <fieldset>
				<TextInput model={member} name="civicregno" title="Personnummer" />
			    </fieldset>
		</div>
		
		<div className="uk-section">
    			<div className="uk-container">
				<h2>3. Konfigurera nyckel </h2>
				Läs av RFID-taggens unika nummer med hjälp av läsaren. 		
			</div>
		
			    <fieldset>
				<TextInput model={member} name="civicregno" title="RFID-tagg" />
			    </fieldset>
		</div>
		</form>

		<div className="uk-section">
    			<div className="uk-container">
				<h2>4. Spara information</h2>
				Spara informationen till databasen 		
			</div>
			<div className="uk-container">	
                        	<button className="uk-button uk-button-success uk-float-left" disabled={saveDisabled}><i className="uk-icon-save"/> {member.id ? 'Spara' : 'Skapa'}</button>
			</div>
		</div>


            </div>
        );
    }
}


export default withRouter(KeyHandoutForm);
